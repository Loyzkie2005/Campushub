"""Read-only Super Admin monitoring and isolated, file-backed research views."""
import csv
from django.contrib import messages
from datetime import date
from decimal import InvalidOperation
from urllib.parse import urlencode

from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.http import Http404, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from accounts.models import Department, ProgramMajor
from api.models import BundleRecommendation, Product
from .services.bundle_suggestions import (build_bundle_suggestions, can_view_bundle_suggestions,
    research_dataset, thresholds, saved_synthetic_research, execute_synthetic_research)
from .services.bundle_monitoring import (history_for, highlight, is_super_monitor,
                                         presentation, recommendations_for, status_records_for,
                                         activity_summary, activity_events_for,
                                         workspace_analysis_summary, recommendation_evidence)

TEMPLATE = "marketplace/pages/bundle_monitoring.html"
DETAIL_TEMPLATE = "marketplace/partials/bundle_monitor_details.html"


def uses_analysis_workspace(user):
    return not is_super_monitor(user) and user.role.strip().lower() == "marketplace admin"


def can_send_suggestion(user, item):
    """Use the existing detail-page visibility rules; highlight rechecks on POST."""
    return (not is_super_monitor(user) and user.has_perm("accounts.can_manage_sellers")
            and bool(item["record"].product_a.mobile_seller_id) and item["eligible"]
            and not item["record"].sent_at)


def annotated(user):
    return status_records_for(user)


@never_cache
@require_GET
def recommendation_activity(request):
    if not can_view_bundle_suggestions(request.user):
        raise PermissionDenied
    try:
        activity = activity_summary(request.user)
        current = Paginator(activity_events_for(request.user), 20).get_page(request.GET.get("page"))
        events = list(current)
        records = {row.pk: row for row in recommendations_for(request.user).filter(
            pk__in={event.recommendation_key for event in events})}
        rows = [{"event": event, "recommendation": records[event.recommendation_key]} for event in events]
        return page(request, mode="activity", heading="Recommendation Activity", activity=activity, rows=rows, current=current)
    except DatabaseError:
        return page(request, mode="error", heading="Recommendation Activity", http_status=503,
                    failure="Unable to load recommendation activity. Please retry.", retry_url=request.path)


def context(request, **extra):
    return {"super_monitor": is_super_monitor(request.user), **extra}


@timezone.override("Asia/Manila")
def page(request, **extra):
    response = render(request, TEMPLATE, context(request, **extra), status=extra.get("http_status", 200))
    response["Cache-Control"] = "private, no-store"
    return response


@never_cache
@require_GET
@timezone.override("Asia/Manila")
def suggestion_list(request):
    if not can_view_bundle_suggestions(request.user):
        raise PermissionDenied
    # Source navigation is presentation only. Never use the calculate-on-miss
    # synthetic cache here, including for Super Admin page requests.
    recommendation_view = "dataset" if request.GET.get("view") == "dataset" else "live"
    source_args = request.GET.copy()
    source_args.pop("page", None)
    source_args["view"] = "dataset"
    dataset_url = "?" + source_args.urlencode()
    source_args["view"] = "live"
    live_url = "?" + source_args.urlencode()
    source_context = dict(recommendation_view=recommendation_view,
                          dataset_url=dataset_url, live_url=live_url)
    if recommendation_view == "dataset":
        return page(request, mode="list", heading="Suggested Product Bundle", **source_context)
    try:
        base = annotated(request.user)
        summary = {"total": base.count(), "sent": base.filter(sent_at__isnull=False).count(),
                   "created": base.filter(_created=True).count(),
                   "awaiting": base.filter(sent_at__isnull=False, _created=False, _dismissed=False, _accepted=False).count()}
        rows = base.annotate(_web_name=Concat("product_a__seller__first_name", Value(" "), "product_a__seller__last_name"),
                             _mobile_name=Concat("product_a__mobile_seller__first_name", Value(" "), "product_a__mobile_seller__last_name"))
        query = request.GET.get("q", "").strip()[:150]
        if query:
            search = Q(product_a__name__icontains=query) | Q(product_b__name__icontains=query) | Q(
                product_a__seller__first_name__icontains=query) | Q(product_a__seller__last_name__icontains=query) | Q(
                product_a__seller__username__icontains=query) | Q(product_a__mobile_seller__first_name__icontains=query) | Q(
                product_a__mobile_seller__last_name__icontains=query) | Q(product_a__mobile_seller__username__icontains=query)
            search |= Q(_web_name__icontains=query) | Q(_mobile_name__icontains=query)
            if query.isdecimal() and len(query) <= 18:
                search |= Q(pk=int(query))
            rows = rows.filter(search)
        for key in ("program", "major"):
            value = request.GET.get(key, "").strip()
            if value:
                if not value.isdecimal() or len(value) > 18:
                    rows = rows.none()
                else:
                    field = "department_id" if key == "program" else "major_id"
                    rows = rows.filter(Q(**{f"product_a__seller__{field}": int(value)}) |
                                       Q(**{f"product_a__mobile_seller__{field}": int(value)}))
        seller = request.GET.get("seller", "").strip()
        if seller:
            source, _, identity = seller.partition(":")
            if source not in {"admin", "mobile"} or not identity.isdecimal() or len(identity) > 18:
                rows = rows.none()
            else:
                rows = rows.filter(**{"product_a__" + ("seller_id" if source == "admin" else "mobile_seller_id"): int(identity)})
        state = request.GET.get("response", "").strip()
        if state == "created":
            rows = rows.filter(_created=True)
        elif state == "dismissed":
            rows = rows.filter(_created=False, _dismissed=True)
        elif state == "awaiting":
            rows = rows.filter(_created=False, _dismissed=False, _accepted=False, sent_at__isnull=False)
        elif state == "accepted":
            rows = rows.filter(_created=False, _dismissed=False, _accepted=True, sent_at__isnull=False)
        elif state == "na":
            rows = rows.filter(_created=False, _dismissed=False, sent_at__isnull=True)
        elif state:
            rows = rows.none()
        error = ""
        dates = {}
        for key, lookup in (("start", "generated_at__date__gte"), ("end", "generated_at__date__lte")):
            value = request.GET.get(key, "").strip()
            if value:
                try:
                    dates[key] = date.fromisoformat(value)
                    rows = rows.filter(**{lookup: dates[key]})
                except ValueError:
                    rows, error = rows.none(), "Enter valid generated dates."
        if "start" in dates and "end" in dates and dates["start"] > dates["end"]:
            rows, error = rows.none(), "Generated from must be on or before Generated through."
        paginator = Paginator(rows, 1)
        current = paginator.get_page(request.GET.get("page"))
        sellers = {}
        owner_fields = [f"product_a__{source}__{field}" for source in ("seller", "mobile_seller")
                        for field in ("id", "first_name", "last_name", "username")]
        for identity in base.order_by().values_list(*owner_fields).distinct():
            mobile = identity[4] is not None
            pk, first, last, username = identity[4:] if mobile else identity[:4]
            sellers[f"{'mobile' if mobile else 'admin'}:{pk}"] = f"{first or ''} {last or ''}".strip() or username
        args = request.GET.copy()
        args.pop("page", None)
        workspace = uses_analysis_workspace(request.user)
        slides = [presentation(row) for row in current]
        for item in slides:
            item["can_send"] = can_send_suggestion(request.user, item)
        return page(request, mode="list", heading="Suggested Product Bundle", summary=summary, **source_context,
            rows=slides, current=current, query_args=args.urlencode(),
            carousel_pages=paginator.get_elided_page_range(current.number, on_each_side=2, on_ends=1),
            programs=Department.objects.filter(is_program=True), majors=ProgramMajor.objects.all(),
            sellers=sorted(sellers.items(), key=lambda item: item[1].casefold()), form_error=error,
            workspace=workspace, analysis=workspace_analysis_summary(request.user) if workspace else None,
            has_active_filters=bool(query or any(request.GET.get(key, "").strip()
                for key in ("program", "major", "seller", "response", "start", "end"))))
    except DatabaseError:
        return page(request, mode="error", heading="Suggested Product Bundle", http_status=503,
                    failure="Unable to load recommendations. Please retry or ask the administrator to check the database.")


@never_cache
@require_GET
def suggestion_detail(request, pk, section="details"):
    if section not in {"details", "response", "history", "bundle"}:
        raise Http404
    drawer = request.GET.get("format") == "drawer"
    try:
        row = get_object_or_404(recommendations_for(request.user), pk=pk)
        workspace = uses_analysis_workspace(request.user)
        if drawer and section != "details":
            raise Http404
        item = presentation(row)
        events = Paginator(history_for(row), 25).get_page(request.GET.get("page"))
        can_highlight = can_send_suggestion(request.user, item)
        evidence = recommendation_evidence(row)
        if drawer:
            response = render(request, DETAIL_TEMPLATE, {"item": item, "current": events,
                "evidence": evidence, "can_highlight": can_highlight})
            response["Cache-Control"] = "private, no-store"
            return response
        return page(request, mode=section, heading={"details": "Suggestion Details", "response": "Seller Response",
            "history": "Recommendation History", "bundle": "Created Bundles"}[section], item=item, current=events,
            can_highlight=can_highlight, workspace=workspace, evidence=evidence)
    except DatabaseError:
        return page(request, mode="error", heading="Suggestion Details", http_status=503,
                    failure="Unable to load this suggestion. Please retry.")


@never_cache
@require_POST
def suggestion_highlight(request, pk):
    json_request = "application/json" in request.headers.get("Accept", "")
    try:
        row = highlight(request, pk)
        if json_request:
            item = presentation(row)
            status = "Awaiting Seller Response" if item["response"] == "Awaiting Response" else item["response"]
            return JsonResponse({"id": row.pk, "sent": bool(row.sent_at), "status": status})
    except ValidationError as exc:
        if json_request:
            return JsonResponse({"error": " ".join(exc.messages)}, status=409)
        return page(request, mode="error", heading="Suggestion unavailable", http_status=409, failure=" ".join(exc.messages))
    except BundleRecommendation.DoesNotExist:
        if json_request:
            return JsonResponse({"error": "This suggestion is no longer available in your scope."}, status=404)
        raise Http404
    except PermissionDenied:
        if json_request:
            return JsonResponse({"error": "You are not authorized to send this suggestion."}, status=403)
        raise
    except DatabaseError:
        if json_request:
            return JsonResponse({"error": "Unable to confirm sending. Please retry; an already recorded send will not be duplicated."}, status=503)
        raise
    messages.success(request, "Recommendation highlighted in the seller workspace. No push notification or email was sent.")
    return redirect("bundle_monitor_detail", pk=pk)


def _analysis_selection(request):
    """Keep legacy role defaults/tab links; use separate source and result tabs."""
    legacy = request.GET.get('tab', '')
    source = request.GET.get('source', '')
    if source not in {'marketplace', 'live', 'synthetic'}:
        source = legacy if legacy in {'marketplace', 'synthetic'} else (
            'synthetic' if is_super_monitor(request.user) else 'marketplace')
    return ('marketplace' if source == 'live' else source,
            'results' if legacy == 'results' else 'dataset')


def _analysis_args(request, source, tab, *, reset_pages=False, remove_page='page'):
    args = request.GET.copy()
    args['source'], args['tab'] = source, tab
    args.pop(remove_page, None)
    if reset_pages:
        args.pop('page', None)
        args.pop('itemsets_page', None)
    return args.urlencode()


def _matching_records(records, query):
    return [row for row in records if query.casefold() in
            ' '.join(str(value) for value in row.values()).casefold()] if query else records


def _render_analysis(request, *, source=None, tab=None, failure=''):
    selected_source, selected_tab = _analysis_selection(request)
    source, tab = source or selected_source, tab or selected_tab
    super_admin = is_super_monitor(request.user)
    query = request.GET.get('q', '').strip()[:150]
    data = dict(mode='research', heading='Dataset & Apriori Analysis', workspace=False,
        dataset_source=source, tab=tab, query=query, rows=[], analysis=None,
        restricted=source == 'synthetic' and not super_admin,
        can_execute=source == 'synthetic' and super_admin,
        source_marketplace_url='?' + _analysis_args(request, 'marketplace', 'dataset', reset_pages=True),
        source_synthetic_url='?' + _analysis_args(request, 'synthetic', 'dataset', reset_pages=True),
        preview_url='?' + _analysis_args(request, source, 'dataset', reset_pages=True),
        results_url='?' + _analysis_args(request, source, 'results', reset_pages=True),
        run_query_args=_analysis_args(request, 'synthetic', 'results', reset_pages=True),
        query_args=_analysis_args(request, source, tab),
        itemsets_query_args=_analysis_args(request, source, tab, remove_page='itemsets_page'),
        statistics=[{'label': 'Transactions' if source == 'synthetic' else 'Eligible Transactions / Baskets', 'value': None},
                    {'label': 'Order Items', 'value': None}, {'label': 'Unique Products', 'value': None}],
        analysis_error=failure, http_status=503 if failure else 200)
    try:
        if source == 'marketplace':
            analysis = workspace_analysis_summary(request.user)
            data['analysis'] = analysis
            data['statistics'][0]['value'] = analysis['basket_count']
            if analysis['state'] == 'unavailable':
                data.update(analysis_error='Unable to load saved analysis. Please retry.', http_status=503)
        elif super_admin and not failure:
            snapshot = research_dataset()  # Validated CSV/metadata only; never mines.
            for field, key in zip(data['statistics'], ('transaction_count', 'item_count', 'unique_product_count')):
                field['value'] = snapshot[key]
            if tab == 'dataset':
                records = _matching_records(snapshot['records'], query)
                current = Paginator(records, 20).get_page(request.GET.get('page'))
                data.update(columns=snapshot['columns'], current=current, preview_available=True,
                            dataset_page=[list(row.values()) for row in current])
            else:
                saved = saved_synthetic_research(request.user, snapshot, thresholds())
                if saved:
                    result = saved['result']
                    current = Paginator(_matching_records(result['directional_rows'], query), 20).get_page(request.GET.get('page'))
                    itemsets = Paginator(_matching_records(result['frequent_itemsets'], query), 20).get_page(request.GET.get('itemsets_page'))
                    data.update(result=result, current=current, itemsets_current=itemsets,
                                analysis_completed_at=saved['completed_at'])
    except (OSError, ValueError, InvalidOperation, csv.Error, DatabaseError):
        data.update(analysis_error='Synthetic transaction dataset is unavailable. Please retry.'
                    if source == 'synthetic' else 'Unable to load saved analysis. Please retry.', http_status=503)
    return page(request, **data)


@never_cache
@require_GET
def research(request):
    if (not can_view_bundle_suggestions(request.user)
            or not (is_super_monitor(request.user) or uses_analysis_workspace(request.user))):
        raise PermissionDenied
    return _render_analysis(request)


def readonly_analysis(request):
    """Compatibility wrapper; the common view retains GET and permission checks."""
    return research(request)


@never_cache
@require_POST
def run_research(request):
    if not is_super_monitor(request.user):
        raise PermissionDenied
    try:
        execute_synthetic_research(request.user)
    except (OSError, ValueError, InvalidOperation, csv.Error):
        return _render_analysis(request, source='synthetic', tab='results',
                                failure='Unable to complete synthetic analysis. Please check the dataset and retry.')
    return redirect(reverse_research_results(request.GET))


def reverse_research_results(params=None):
    from django.urls import reverse
    args = params.copy() if params is not None else {}
    args.update(source='synthetic', tab='results')
    args.pop('page', None)
    args.pop('itemsets_page', None)
    return reverse('bundle_monitor_research') + '?' + urlencode(args)
