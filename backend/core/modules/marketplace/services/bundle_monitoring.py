"""Persist live evidence on explicit refresh; monitoring GETs never write records."""
from math import isfinite
from types import SimpleNamespace
from uuid import UUID, uuid4
from zoneinfo import ZoneInfo

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import connection, transaction, DatabaseError
from django.db.models import Q, Count, Exists, OuterRef, F, Value, CharField, Subquery
from django.db.models.functions import JSONArray, JSONObject, Cast, Concat, Coalesce
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.dateformat import format as date_format

from accounts.academic import academic_labels, scope_products, has_valid_marketplace_scope
from accounts.activity_logging import log_marketplace_event
from accounts.models import AccountActivity, Department, ProgramMajor
from api.models import BundleRecommendation, Product, SellerBundleSuggestion, SellerRequest
from .bundle_suggestions import build_bundle_suggestions, can_view_bundle_suggestions

ANALYSIS_COMPLETED = 'BUNDLE_ANALYSIS_COMPLETED'
ANALYSIS_VERSION = 1


def _analysis_outcome(baskets, multi, recommendations):
    from .analytics import MARKET_BASKET_MIN_ORDERS, MARKET_BASKET_MIN_MULTI_ITEM_ORDERS
    if recommendations:
        return 'recommendations'
    if baskets < MARKET_BASKET_MIN_ORDERS or multi < MARKET_BASKET_MIN_MULTI_ITEM_ORDERS:
        return 'insufficient_data'
    return 'no_recommendations'


def _record_analysis_completion(actor, result, seen):
    """Write one atomic run/scope snapshot after recommendation persistence.

    Scoped rows describe the processed subset of a marketplace-wide run, never
    a separately mined result or a newly recalculated current-order count.
    """
    baskets, multi = result.get('transaction_count'), result.get('multi_item_count')
    cohorts = result.get('_analysis_basket_scopes')
    if (type(baskets) is not int or baskets < 0 or type(multi) is not int
            or not 0 <= multi <= baskets or not isinstance(cohorts, list)):
        raise ValidationError('Analysis scope evidence is incomplete; existing records were preserved.')
    totals = {}
    for cohort in cohorts:
        if not isinstance(cohort, dict):
            raise ValidationError('Invalid analysis scope evidence.')
        program, major = cohort.get('program_id'), cohort.get('major_id')
        count, multiple = cohort.get('baskets'), cohort.get('multi_item_baskets')
        if (any(value is not None and (type(value) is not int or value <= 0) for value in (program, major))
                or type(count) is not int or count < 0 or type(multiple) is not int
                or not 0 <= multiple <= count or (program, major) in totals):
            raise ValidationError('Conflicting analysis scope evidence.')
        totals[(program, major)] = (count, multiple)
    if sum(value[0] for value in totals.values()) != baskets or sum(value[1] for value in totals.values()) != multi:
        raise ValidationError('Analysis basket totals do not reconcile; existing records were preserved.')

    # The existing refresh advisory lock serializes runs. Reject a repeated run
    # identity instead of producing a second/conflicting completion snapshot.
    run_id = str(uuid4())
    if AccountActivity.objects.filter(activity_type=ANALYSIS_COMPLETED, metadata__run_id=run_id).exists():
        raise ValidationError('This analysis completion has already been recorded.')
    completed_at = timezone.now()
    records = list(BundleRecommendation.objects.filter(pk__in=set(seen)).select_related(
        'product_a__seller', 'product_a__mobile_seller', 'product_b__seller', 'product_b__mobile_seller'))

    def academic(product):
        owner = product.owner
        return (product.department_id or owner.department_id,
                product.major_id if product.department_id else owner.major_id)

    pairs = [(academic(row.product_a), academic(row.product_b)) for row in records]
    scopes = [('global', None, None, baskets, multi, len(records))]
    for program in Department.objects.filter(is_program=True).order_by('pk'):
        count = sum(value[0] for key, value in totals.items() if key[0] == program.pk)
        multiple = sum(value[1] for key, value in totals.items() if key[0] == program.pk)
        qualified = sum(a[0] == program.pk and b[0] == program.pk for a, b in pairs)
        scopes.append(('program', program.pk, None, count, multiple, qualified))
    for major in ProgramMajor.objects.filter(program__is_program=True).order_by('pk'):
        count, multiple = totals.get((major.program_id, major.pk), (0, 0))
        qualified = sum(a == b == (major.program_id, major.pk) for a, b in pairs)
        scopes.append(('major', major.program_id, major.pk, count, multiple, qualified))
    request = SimpleNamespace(user=actor, META={})
    for kind, program, major, count, multiple, qualified in scopes:
        log_marketplace_event(request, account=actor, source='admin', activity_type=ANALYSIS_COMPLETED,
            activity='Live bundle analysis completed.', metadata={
                'analysis_version': ANALYSIS_VERSION, 'run_id': run_id, 'source': 'live',
                'completed_at': completed_at.isoformat(), 'analysis_scope': 'marketplace',
                'scope': {'kind': kind, 'program_id': program, 'major_id': major},
                'basket_count': count, 'multi_item_basket_count': multiple,
                'recommendation_count': qualified, 'outcome': _analysis_outcome(count, multiple, qualified),
            })


def _saved_analysis_summary(user, *, workspace=False):
    """Only saved, validated completion evidence for the reader's exact scope."""
    if not can_view_bundle_suggestions(user):
        raise PermissionDenied
    global_scope = bool(user.is_superuser)
    if not workspace and (global_scope or user.role.strip().lower() == 'super admin'):
        return None
    missing = {'state': 'unrecorded', 'basket_count': None, 'completed_at': None,
               'source_label': 'No Analysis Yet', 'history_label': 'Analysis history not recorded',
               'note': 'No completed live analysis has been recorded for your scope.'}
    if not (workspace and global_scope) and not has_valid_marketplace_scope(user):
        return missing
    try:
        event = AccountActivity.objects.filter(module='Marketplace', result=AccountActivity.RESULT_SUCCESS,
            activity_type=ANALYSIS_COMPLETED, metadata__analysis_version=ANALYSIS_VERSION,
            metadata__source='live', metadata__scope__kind=(
                'global' if workspace and global_scope else 'major' if user.major_id else 'program'),
            metadata__scope__program_id=None if workspace and global_scope else user.department_id,
            metadata__scope__major_id=None if workspace and global_scope else user.major_id,
        ).order_by('-created_at', '-pk').first()
    except DatabaseError:
        return {**missing, 'state': 'unavailable', 'source_label': 'Unavailable',
                'history_label': 'Analysis history unavailable', 'note': 'Unable to load analysis history.'}
    if not event:
        return missing
    data = event.metadata
    try:
        UUID(data['run_id'])
        if workspace:
            expected_scope = {'kind': 'global' if global_scope else 'major' if user.major_id else 'program',
                              'program_id': None if global_scope else user.department_id,
                              'major_id': None if global_scope else user.major_id}
            scope = data.get('scope')
            if (type(data.get('analysis_version')) is not int or data['analysis_version'] != ANALYSIS_VERSION
                    or data.get('source') != 'live' or not isinstance(scope, dict)
                    or scope != expected_scope
                    or any(type(scope[key]) is not int for key in ('program_id', 'major_id')
                           if expected_scope[key] is not None)):
                return missing
        completed_at = parse_datetime(data['completed_at'])
        count, multi, qualified = data['basket_count'], data['multi_item_basket_count'], data['recommendation_count']
        if (data.get('analysis_scope') != 'marketplace' or completed_at is None or timezone.is_naive(completed_at)
                or type(count) is not int or count < 0 or type(multi) is not int or not 0 <= multi <= count
                or type(qualified) is not int or qualified < 0
                or data['outcome'] not in ('recommendations', 'no_recommendations', 'insufficient_data')
                or (data['outcome'] == 'recommendations') != (qualified > 0)):
            return missing
    except (KeyError, TypeError, ValueError, AttributeError):
        return missing
    notes = {'insufficient_data': 'Insufficient multi-product basket data for reliable suggestions.',
             'no_recommendations': 'Analysis completed with no qualifying suggestions in your scope.',
             'recommendations': 'Analysis completed; eligible saved suggestions appear above.'}
    return {**({'multi_item_basket_count': multi} if workspace else {}),
            'state': data['outcome'], 'basket_count': count, 'completed_at': completed_at.isoformat(),
            'completed_label': date_format(timezone.localtime(completed_at, ZoneInfo('Asia/Manila')), 'M j, Y · g:i A'),
            'source_label': 'Marketplace Orders', 'history_label': '',
            'note': notes[data['outcome']],
            'scope_note': 'Baskets in your scope from the saved marketplace-wide analysis.'}


def saved_analysis_summary(user):
    """Preserve the original dashboard projection, including its exact keys."""
    return _saved_analysis_summary(user)


def workspace_analysis_summary(user):
    """Read saved completion evidence only, never mine or infer a denominator.

    Saved pair counts are not raw association-rule counts. Even a completed
    no-recommendations outcome cannot establish that no raw rules existed.
    """
    saved = _saved_analysis_summary(user, workspace=True)
    recorded = saved['completed_at'] is not None
    return {**saved,
            'multi_item_basket_count': saved.get('multi_item_basket_count'),
            'completed_label': saved['completed_label'] if recorded else None,
            'source_label': saved['source_label'] if recorded else ('Unavailable' if saved['state'] == 'unavailable' else 'Not recorded'),
            'outcome_label': {
                'recommendations': 'Saved suggestions recorded',
                'no_recommendations': 'No qualifying saved suggestions',
                'insufficient_data': 'Insufficient transaction data',
                'unrecorded': 'Historical analysis information unavailable',
                'unavailable': 'Analysis history unavailable',
            }[saved['state']],
            'scope_note': ('Marketplace-wide saved analysis.' if user.is_superuser else
                           'Baskets in your scope from the saved marketplace-wide analysis.'),
            'rule_count': None,
            'rules_state': 'unavailable' if saved['state'] == 'unavailable' else 'not_recorded',
            'rules_title': {'unrecorded': 'Analysis history not recorded',
                            'insufficient_data': 'Insufficient transaction-basket data',
                            'unavailable': 'Analysis history unavailable'}.get(saved['state'], 'Association rules not recorded'),
            'rules_note': ('Raw association rules and their count were not saved. Saved product pairs '
                           'cannot reconstruct the full rule table or its denominator.')}


def recommendation_evidence(row):
    """Validate original stored directional evidence, not latest verification.

    Refresh updates verified_at but does not update metrics. No supporting basket
    count, analysis-run date or source provenance is recoverable from these pairs.
    """
    result = {'state': 'unavailable', 'available': False, 'antecedent': None, 'consequent': None,
              'antecedent_id': None, 'consequent_id': None,
              'antecedent_name': None, 'consequent_name': None,
              'support': None, 'confidence': None, 'lift': None,
              'supporting_basket_count': None, 'analysis_run_at': None,
              'source_label': None, 'evidence_label': 'Original stored evidence',
              'note': ('Original stored pair metrics, not latest verification. Supporting basket count, '
                       'analysis-run date and source provenance are not recorded.')}
    metrics = row.metrics
    if not isinstance(metrics, dict):
        return result
    values = [metrics.get(key) for key in ('support', 'confidence', 'lift')]
    if any(type(value) not in (int, float) for value in values):
        return result
    try:
        if not all(isfinite(value) for value in values):
            return result
    except OverflowError:
        return result
    support, confidence, lift = values
    if not (0 <= support <= 100 and 0 <= confidence <= 100 and lift > 0):
        return result
    # The adapter originally stores decimal string IDs. Accept only canonical
    # positive integer identities, never bools, floats or synthetic identifiers.
    def identity(value):
        if type(value) is int and value > 0:
            return value
        if isinstance(value, str) and len(value) <= 20 and value.isascii() and value.isdecimal() and str(int(value)) == value:
            return int(value) if int(value) > 0 else None
        return None

    a, b = identity(metrics.get('product_a_id')), identity(metrics.get('product_b_id'))
    if a is None or b is None or a == b or {a, b} != {row.product_a_id, row.product_b_id}:
        return result
    products = {row.product_a_id: row.product_a, row.product_b_id: row.product_b}
    return {**result, 'state': 'recorded', 'available': True,
            'antecedent': products[a].name, 'consequent': products[b].name,
            'antecedent_id': a, 'consequent_id': b,
            'antecedent_name': products[a].name, 'consequent_name': products[b].name,
            'support': support, 'confidence': confidence, 'lift': lift}


def is_super_monitor(user):
    # Canonical global scope is is_superuser, not a client-supplied role label.
    return bool(user.is_authenticated and user.is_superuser and can_view_bundle_suggestions(user))


def recommendations_for(user):
    if not can_view_bundle_suggestions(user):
        raise PermissionDenied
    products = scope_products(Product.objects.all(), user).values("pk")
    return BundleRecommendation.objects.filter(product_a_id__in=products, product_b_id__in=products).select_related(
        "product_a__seller__department", "product_a__seller__major", "product_a__mobile_seller__department",
        "product_a__mobile_seller__major", "product_b__seller", "product_b__mobile_seller", "sent_by"
    ).prefetch_related("created_bundles", "product_a__mobile_seller__bundle_suggestion_choices")


def status_records_for(user):
    """One row per recommendation, despite multiple choices, events or bundles."""
    choices = SellerBundleSuggestion.objects.filter(seller_id=OuterRef("product_a__mobile_seller_id"),
        product_a_id=OuterRef("product_a_id"), product_b_id=OuterRef("product_b_id"), state="dismissed")
    bundles = linked_bundles_for(recommendations_for(user)).filter(source_recommendation_id=OuterRef("pk"))
    return recommendations_for(user).annotate(_dismissed=Exists(choices), _created=Exists(bundles))


def linked_bundles_for(records):
    return Product.objects.filter(source_recommendation_id__in=records.values("pk"), product_type=Product.TYPE_BUNDLE).filter(
        Q(seller__isnull=False, seller_id=F("source_recommendation__product_a__seller_id")) |
        Q(mobile_seller__isnull=False, mobile_seller_id=F("source_recommendation__product_a__mobile_seller_id")))


def activity_events_for(user):
    """Match existing audits to authorized pairs without importing or duplicating events."""
    records = recommendations_for(user).order_by()
    direct = records.annotate(_event_key=JSONObject(recommendation_id=F("pk"))).filter(
        _event_key__contained_by=OuterRef("metadata"))
    legacy = records.filter(product_a__mobile_seller_id=F("product_b__mobile_seller_id")).annotate(
        _event_key=JSONObject(product_ids=JSONArray(F("product_a_id"), F("product_b_id"))),
        _owner_ref=Concat(Value("mobile:"), Cast("product_a__mobile_seller_id", CharField()))
    ).filter(_event_key__contained_by=OuterRef("metadata"), _owner_ref=OuterRef("account_ref"))
    return AccountActivity.objects.filter(module="Marketplace", result=AccountActivity.RESULT_SUCCESS,
        activity_type__in=("BUNDLE_SUGGESTION_HIGHLIGHTED", "BUNDLE_CREATED_FROM_SUGGESTION", "BUNDLE_SUGGESTION_UPDATED")
    ).annotate(recommendation_key=Coalesce(Subquery(direct.values("pk")[:1]),
        Subquery(legacy.values("pk")[:1]))).filter(recommendation_key__isnull=False).order_by("-created_at", "-pk")


def activity_summary(user, *, include_rates=False):
    records = status_records_for(user)
    counts = dict(sent=Count("pk", filter=Q(sent_at__isnull=False)),
        awaiting=Count("pk", filter=Q(sent_at__isnull=False, _created=False, _dismissed=False)),
        dismissed=Count("pk", filter=Q(_created=False, _dismissed=True)))
    if include_rates:
        counts.update(responded=Count("pk", filter=Q(sent_at__isnull=False) & (Q(_created=True) | Q(_dismissed=True))),
                      created_from_sent=Count("pk", filter=Q(sent_at__isnull=False, _created=True)))
    summary = records.aggregate(**counts)
    rates = None
    if include_rates:
        responded, created = summary.pop("responded"), summary.pop("created_from_sent")
        sent = summary["sent"]
        rates = {"sent": sent, "responded": responded, "created": created,
                 "response_rate": round(responded / sent * 100, 1) if sent else None,
                 "creation_rate": round(created / sent * 100, 1) if sent else None}
    # Counts actual bundle products; repeated audit entries cannot inflate this.
    summary["created"] = linked_bundles_for(records).count()
    result = {"summary": summary, "has_activity": any(summary.values()) or activity_events_for(user).exists(), "error": False}
    if include_rates:
        result["rates"] = rates
    return result


def record_event(request, row, kind, text, **metadata):
    product = row.product_a
    return log_marketplace_event(request, account=product.owner,
        source="mobile" if product.mobile_seller_id else "admin", activity_type=kind, activity=text,
        metadata={"recommendation_id": row.pk, "product_ids": [row.product_a_id, row.product_b_id], **metadata})


@transaction.atomic
def refresh_live(actor):
    if not is_super_monitor(actor):
        raise PermissionDenied
    # Serializes concurrent explicit refreshes without writing on page views.
    with connection.cursor() as cursor:
        cursor.execute("SELECT pg_advisory_xact_lock(%s)", [782465712])
    result = build_bundle_suggestions(actor, source="live")
    if result["error"] or result.get("source") != "live":
        raise ValidationError("Unable to analyze live orders. Existing records were preserved.")
    seen, added = [], 0
    request = SimpleNamespace(user=actor, META={})
    for rule in result["rows"]:
        ids = sorted(int(product["id"]) for product in rule["products"])
        products = list(Product.objects.filter(pk__in=ids).order_by("pk"))
        if len(products) != 2 or products[0].owner_ref != products[1].owner_ref:
            continue
        row, created = BundleRecommendation.objects.get_or_create(product_a_id=ids[0], product_b_id=ids[1],
            defaults={"metrics": {key: rule[key] for key in ("support", "confidence", "lift",
                "product_a_id", "product_b_id")}})
        seen.append(row.pk)
        row.verified_at = timezone.now()
        row.is_current = True
        row.save(update_fields=["verified_at", "is_current"])
        if created:
            added += 1
            record_event(request, row, "BUNDLE_SUGGESTION_GENERATED", "Bundle suggestion generated from live orders.")
    BundleRecommendation.objects.exclude(pk__in=seen).update(is_current=False)
    _record_analysis_completion(actor, result, seen)
    return {"created": added, "current": len(seen), "transactions": result["transaction_count"]}


def eligible_pair(row):
    from .bundles import eligible_component
    a, b = row.product_a, row.product_b
    if a.owner_ref != b.owner_ref or not row.is_current:
        return False
    if not all(eligible_component(product, a.owner_key) for product in (a, b)):
        return False
    owner = a.owner
    if not owner.is_active or owner.is_suspended:
        return False
    owner_filter = {"mobile_user": owner} if a.mobile_seller_id else {"user": owner}
    return SellerRequest.objects.filter(**owner_filter, status="approved", is_suspended=False).exists()


def presentation(row):
    a, b = row.product_a, row.product_b
    owner = a.owner
    academic = academic_labels(owner.department, owner.major)
    bundles = [product for product in row.created_bundles.all()
               if product.product_type == Product.TYPE_BUNDLE and product.owner_ref == a.owner_ref]
    choice = None
    if a.mobile_seller_id and a.owner_ref == b.owner_ref:
        choice = next((item for item in owner.bundle_suggestion_choices.all()
            if (item.product_a_id, item.product_b_id) == (a.pk, b.pk)), None)
    response = "Bundle Created" if bundles else "Dismissed" if choice and choice.state == "dismissed" else (
        "Awaiting Response" if row.sent_at else "Not Applicable")
    photos = []
    for product in (a, b):
        images = product.get_image_list()
        photos.append({"id": product.pk, "name": product.name, "image_url": images[0] if images else "",
                       "category": product.category, "price": product.price,
                       "availability": "Archived" if product.is_archived else product.get_approval_status_display()})
    return {"record": row, "id": row.pk, "products": photos,
            "product_a": a.name, "product_b": b.name, "seller": owner.get_full_name() or owner.username,
            "seller_ref": a.owner_ref, "academic": academic, "response": response,
            "response_at": bundles[0].submitted_at if bundles else choice.updated_at if choice and choice.state == "dismissed" else None,
            "delivery": "Highlighted in seller workspace" if row.sent_at else "Not Sent to Seller",
            "bundles": bundles, "eligible": eligible_pair(row)}


def history_for(row):
    # Existing seller audit events are reused, including those predating stable IDs.
    owner = row.product_a
    account_ref = f"{'mobile' if owner.mobile_seller_id else 'admin'}:{owner.owner.pk}"
    return AccountActivity.objects.filter(module="Marketplace").filter(
        Q(metadata__recommendation_id=row.pk) |
        Q(account_ref=account_ref, activity_type="BUNDLE_SUGGESTION_UPDATED",
          metadata__product_ids=[row.product_a_id, row.product_b_id])
    ).order_by("created_at", "pk")


@transaction.atomic
def highlight(request, pk):
    user = request.user
    if is_super_monitor(user) or not can_view_bundle_suggestions(user) or not user.has_perm("accounts.can_manage_sellers"):
        raise PermissionDenied
    row = recommendations_for(user).select_for_update(of=("self",)).get(pk=pk)
    if not row.product_a.mobile_seller_id:
        raise ValidationError("Workspace highlighting is currently supported for mobile sellers only.")
    if not eligible_pair(row):
        raise ValidationError("This recommendation is no longer eligible.")
    live = build_bundle_suggestions(user, source="live")
    pair = {row.product_a_id, row.product_b_id}
    if live["error"] or live.get("source") != "live" or not any({int(p["id"]) for p in item["products"]} == pair for item in live["rows"]):
        raise ValidationError("This recommendation no longer qualifies. Refresh live analysis first.")
    if not row.sent_at:
        row.sent_at, row.sent_by = timezone.now(), user
        row.save(update_fields=["sent_at", "sent_by"])
        record_event(request, row, "BUNDLE_SUGGESTION_HIGHLIGHTED", "Suggestion highlighted in seller workspace.")
    return row


def link_created_bundle(request, product, pair_ids):
    """Called inside the existing validated seller submission transaction only."""
    row = BundleRecommendation.objects.select_for_update().filter(
        product_a_id=min(pair_ids), product_b_id=max(pair_ids), is_current=True).select_related("product_a", "product_b").first()
    if row and product.owner_ref == row.product_a.owner_ref == row.product_b.owner_ref:
        product.source_recommendation = row
        product.save(update_fields=["source_recommendation", "updated_at"])
        record_event(request, row, "BUNDLE_CREATED_FROM_SUGGESTION", "Seller submitted a bundle from this suggestion.", bundle_id=product.pk)
