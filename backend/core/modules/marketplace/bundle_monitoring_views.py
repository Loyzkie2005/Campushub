"""Read-only Super Admin monitoring and isolated, file-backed research views."""
import csv
from django.contrib import messages
from datetime import date
from pathlib import Path
from urllib.parse import urlencode

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import DatabaseError
from django.db.models import Q, Value
from django.db.models.functions import Concat
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET, require_POST

from accounts.models import Department, ProgramMajor
from api.models import BundleRecommendation, Product
from .services.bundle_suggestions import DATASET, build_bundle_suggestions, can_view_bundle_suggestions
from .services.bundle_monitoring import (history_for, highlight, is_super_monitor,
                                         presentation, recommendations_for, status_records_for,
                                         activity_summary, activity_events_for,
                                         workspace_analysis_summary, recommendation_evidence)

TEMPLATE = "marketplace/pages/bundle_monitoring.html"
DETAIL_TEMPLATE = "marketplace/partials/bundle_monitor_details.html"


def uses_analysis_workspace(user):
    return not is_super_monitor(user) and user.role.strip().lower() == "marketplace admin"


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
        return page(request, mode="list", heading="Bundle Recommendations", **source_context)
    try:
        base = annotated(request.user)
        summary = {"total": base.count(), "sent": base.filter(sent_at__isnull=False).count(),
                   "created": base.filter(_created=True).count(),
                   "awaiting": base.filter(sent_at__isnull=False, _created=False, _dismissed=False).count()}
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
            rows = rows.filter(_created=False, _dismissed=False, sent_at__isnull=False)
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
        paginator = Paginator(rows, 20)
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
        return page(request, mode="list", heading="Bundle Recommendations", summary=summary, **source_context,
            rows=[presentation(row) for row in current], current=current, query_args=args.urlencode(),
            programs=Department.objects.filter(is_program=True), majors=ProgramMajor.objects.all(),
            sellers=sorted(sellers.items(), key=lambda item: item[1].casefold()), form_error=error,
            workspace=workspace, analysis=workspace_analysis_summary(request.user) if workspace else None,
            has_active_filters=bool(query or any(request.GET.get(key, "").strip()
                for key in ("program", "major", "seller", "response", "start", "end"))))
    except DatabaseError:
        return page(request, mode="error", heading="Bundle Recommendations", http_status=503,
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
        can_highlight = (not is_super_monitor(request.user) and request.user.has_perm("accounts.can_manage_sellers")
                         and bool(row.product_a.mobile_seller_id) and item["eligible"] and not row.sent_at)
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
    try:
        highlight(request, pk)
    except ValidationError as exc:
        return page(request, mode="error", heading="Suggestion unavailable", http_status=409, failure=" ".join(exc.messages))
    except BundleRecommendation.DoesNotExist:
        raise Http404
    messages.success(request, "Recommendation highlighted in the seller workspace. No push notification or email was sent.")
    return redirect("bundle_monitor_detail", pk=pk)


@never_cache
@require_GET
def research(request):
    if not is_super_monitor(request.user):
        # An explicit separate branch: never call the research GET executor or
        # its lru_cache on behalf of a read-only Marketplace Admin.
        if not can_view_bundle_suggestions(request.user) or not uses_analysis_workspace(request.user):
            raise PermissionDenied
        return readonly_analysis(request)
    result = build_bundle_suggestions(request.user, source="synthetic")
    if result["error"]:
        return page(request, mode="research", heading="Dataset & Apriori Analysis", research_error=result["message"], http_status=503)
    path = Path(getattr(settings, "CAMPUSHUB_SYNTHETIC_ORDER_ITEMS_PATH", "") or DATASET)
    try:
        with path.open(encoding="utf-8-sig", newline="") as stream:
            reader = csv.DictReader(stream)
            columns, dataset = reader.fieldnames, list(reader)
        tab = "results" if request.GET.get("tab") == "results" else "dataset"
        query = request.GET.get("q", "").strip()[:150]
        records = result["directional_rows"] if tab == "results" else dataset
        if query:
            records = [row for row in records if query.casefold() in " ".join(str(v) for v in row.values()).casefold()]
        current = Paginator(records, 20).get_page(request.GET.get("page"))
        return page(request, mode="research", heading="Dataset & Apriori Analysis", result=result, tab=tab,
            filename=path.name, columns=columns, dataset_page=[list(row.values()) for row in current] if tab == "dataset" else [],
            current=current, distinct_products=len({(row["seller_id"], row["product_id"]) for row in dataset}),
            query_args=urlencode({"tab": tab, "q": query}))
    except (OSError, ValueError, csv.Error):
        return page(request, mode="research", heading="Dataset & Apriori Analysis", http_status=503,
                    research_error="Synthetic transaction dataset is unavailable. Please retry.")


def readonly_analysis(request):
    """Project saved authorized evidence only; no CSV, order queries or mining.

    Called only by the GET/permission-checked research view. The synthetic demo
    has no persisted, safely scoped result snapshot, so this branch cannot show
    it by invoking the existing calculate-and-cache helper.
    """
    tab = "synthetic" if request.GET.get("tab") == "synthetic" else "marketplace"
    try:
        analysis = workspace_analysis_summary(request.user)
        records = recommendations_for(request.user)
        query = request.GET.get("q", "").strip()[:150]
        if query:
            records = records.filter(Q(product_a__name__icontains=query) | Q(product_b__name__icontains=query))
        current = Paginator(records if tab == "marketplace" else records.none(), 20).get_page(request.GET.get("page"))
        rows = [{"item": presentation(row), "evidence": recommendation_evidence(row)} for row in current]
        return page(request, mode="analysis_readonly", heading="Dataset & Analysis", workspace=True,
                    analysis=analysis, tab=tab, rows=rows, current=current,
                    query_args=urlencode({"tab": tab, "q": query}))
    except DatabaseError:
        return page(request, mode="error", heading="Dataset & Analysis", http_status=503,
                    failure="Unable to load saved analysis. Please retry.", retry_url=request.path)


@never_cache
@require_POST
def run_research(request):
    if not is_super_monitor(request.user):
        raise PermissionDenied
    from .services.bundle_suggestions import _cached_synthetic
    _cached_synthetic.cache_clear()  # Research-only cache. No live generation or persistence.
    return redirect(reverse_research_results())


def reverse_research_results():
    from django.urls import reverse
    return reverse("bundle_monitor_research") + "?tab=results"
