"""Read-only DRF adapters over the existing CampusHub audit model and RBAC."""
from datetime import datetime, time, timedelta

from django.core.exceptions import PermissionDenied as DjangoPermissionDenied
from django.db import DatabaseError
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework import serializers
from rest_framework.authentication import BaseAuthentication, SessionAuthentication
from rest_framework.exceptions import AuthenticationFailed, NotAuthenticated, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import BasePermission
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.activity_service import format_activities
from accounts.admin_tab_auth import get_tab_token_from_request, get_user_for_tab_token
from accounts.models import AccountActivity, User
from accounts.support_scope import is_marketplace_admin, is_super_admin, support_activity


class ExistingCampusHubAuthentication(BaseAuthentication):
    """Reuse tab authentication and recognize mobile identity without admin access."""
    def authenticate(self, request):
        key = get_tab_token_from_request(request)
        if key:
            user = get_user_for_tab_token(key)
            if user is None:
                raise AuthenticationFailed("Invalid or expired admin login.")
            return user, None
        if request.headers.get("Authorization"):
            # The existing mobile JWT verifies identity only. Permission below
            # explicitly rejects mobile accounts, including mobile Admin types.
            from api.views import _mobile_user_from_bearer
            user, error = _mobile_user_from_bearer(request)
            if error is not None:
                raise AuthenticationFailed("Invalid or expired mobile login.")
            return user, None
        return None

    def authenticate_header(self, request):
        return 'CampusHubTab realm="activity-logs"'


class CanReadActivity(BasePermission):
    message = "You do not have access to user monitoring."

    def has_permission(self, request, view):
        actor = request.user
        if request.successful_authenticator is None:
            raise NotAuthenticated("Authentication required.")
        if not isinstance(actor, User) or not actor.is_active or actor.is_suspended:
            return False
        # Exactly the existing web-page role gate and Django permission.
        return bool((is_super_admin(actor) or is_marketplace_admin(actor))
                    and actor.has_perm("accounts.can_view_user_monitoring"))


class PerformedBySerializer(serializers.Serializer):
    name = serializers.CharField()
    username = serializers.CharField(allow_null=True)
    role = serializers.CharField(allow_null=True)


class AffectedRecordSerializer(serializers.Serializer):
    type = serializers.CharField()
    label = serializers.CharField()
    name = serializers.CharField()


class ConnectionSerializer(serializers.Serializer):
    ip_address = serializers.CharField(allow_null=True)
    device = serializers.CharField()
    browser = serializers.CharField()


class ActivityListSerializer(serializers.Serializer):
    """Explicit output allowlist; raw model metadata can never leak through it."""
    id = serializers.IntegerField()
    date_time = serializers.CharField()
    performed_by = PerformedBySerializer()
    action = serializers.CharField()
    module = serializers.CharField()
    result = serializers.CharField(allow_null=True)


class ActivityDetailSerializer(ActivityListSerializer):
    affected_record = AffectedRecordSerializer(allow_null=True)
    connection = ConnectionSerializer(allow_null=True)


class ActivityPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100

    def get_paginated_response(self, data):
        # Page numbers instead of URL echoes: query-string tab credentials must
        # never be copied into API next/previous response links.
        return Response({"success": True, "data": data, "pagination": {
            "count": self.page.paginator.count, "page": self.page.number,
            "page_size": self.get_page_size(self.request),
            "next_page": self.page.next_page_number() if self.page.has_next() else None,
            "previous_page": self.page.previous_page_number() if self.page.has_previous() else None,
        }})


class ActivityAPIView(APIView):
    authentication_classes = [ExistingCampusHubAuthentication, SessionAuthentication]
    permission_classes = [CanReadActivity]
    renderer_classes = [JSONRenderer]
    http_method_names = ["get", "head", "options"]

    def queryset(self, request):
        # Enforce account/Program/Major/event scope BEFORE any filters or lookup.
        return support_activity(AccountActivity.objects.all(), request.user).order_by("-created_at", "-pk")

    def handle_exception(self, exc):
        if isinstance(exc, DatabaseError):
            return Response({"success": False, "message": "Unable to load activity records. Please retry.", "errors": {}}, status=503)
        if isinstance(exc, DjangoPermissionDenied):
            from rest_framework.exceptions import PermissionDenied
            exc = PermissionDenied(CanReadActivity.message)
        response = super().handle_exception(exc)
        detail = response.data
        messages = {401: "Authentication required or login expired.", 403: CanReadActivity.message,
                    404: "Activity record or page not found.", 400: "Invalid activity filters."}
        response.data = {"success": False, "message": messages.get(response.status_code, "Activity request could not be completed."),
                         "errors": detail if isinstance(detail, dict) and "detail" not in detail else {}}
        return response

    def finalize_response(self, request, response, *args, **kwargs):
        response = super().finalize_response(request, response, *args, **kwargs)
        response["Cache-Control"] = "no-store"
        return response


class ActivityDetailView(ActivityAPIView):
    def get(self, request, pk):
        event = get_object_or_404(self.queryset(request), pk=pk)
        formatted = format_activities([event], scoped=is_marketplace_admin(request.user))[0]
        return Response({"success": True, "data": ActivityDetailSerializer(formatted).data})


class ActivityListView(ActivityAPIView):
    def get(self, request):
        queryset = self.queryset(request)
        params = request.query_params
        search = params.get("search", "").strip()[:200]
        if search:
            queryset = queryset.filter(Q(username__icontains=search) | Q(full_name__icontains=search)
                                       | Q(activity__icontains=search))
        # actor is a human username, not an internal actor primary key.
        actor = params.get("actor", "").strip()[:150]
        if actor:
            actor_ids = list(User.objects.filter(username=actor).values_list("pk", flat=True))
            queryset = queryset.filter(Q(metadata__actor_username=actor)
                | Q(metadata__actor_admin_id__in=actor_ids)
                | Q(module="Authentication", username=actor))
        for key in ("account_type", "role", "activity_type", "result"):
            if params.get(key):
                queryset = queryset.filter(**{key: params[key][:150]})
        module = params.get("module")
        if module:
            from accounts.activity_service import MODULE_LABELS
            names = [name for name, label in MODULE_LABELS.items() if label.casefold() == module.casefold()]
            condition = Q(pk__in=[])
            for name in names:
                condition |= Q(module__iexact=name)
            if module.casefold() == "system":
                known = Q(pk__in=[])
                for name in MODULE_LABELS:
                    known |= Q(module__iexact=name)
                condition |= ~known
            queryset = queryset.filter(condition)
        dates = {}
        for key in ("date_from", "date_to"):
            if params.get(key):
                try:
                    dates[key] = parse_date(params[key])
                except ValueError:
                    dates[key] = None
                if dates[key] is None:
                    raise ValidationError({key: ["Use a valid YYYY-MM-DD date."]})
        if dates.get("date_from") and dates.get("date_to") and dates["date_from"] > dates["date_to"]:
            raise ValidationError({"date_to": ["End date must be on or after start date."]})
        if dates.get("date_from"):
            queryset = queryset.filter(created_at__gte=timezone.make_aware(datetime.combine(dates["date_from"], time.min)))
        if dates.get("date_to"):
            if dates["date_to"].year == 9999 and dates["date_to"].month == 12 and dates["date_to"].day == 31:
                raise ValidationError({"date_to": ["Use an end date before 9999-12-31."]})
            queryset = queryset.filter(created_at__lt=timezone.make_aware(datetime.combine(dates["date_to"] + timedelta(days=1), time.min)))
        pagination = ActivityPagination()
        events = pagination.paginate_queryset(queryset, request, view=self)
        formatted = format_activities(events, scoped=is_marketplace_admin(request.user), include_targets=False)
        return pagination.get_paginated_response(ActivityListSerializer(formatted, many=True).data)
