"""Django's existing authentication with built-in role domain boundaries."""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied

from .role_permissions import role_scope_permissions


class RoleScopeBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        name = username if username is not None else kwargs.get(get_user_model().USERNAME_FIELD)
        if name and get_user_model().objects.filter(username=name, is_suspended=True).exists():
            raise PermissionDenied("Account is disabled.")
        return super().authenticate(request, username, password, **kwargs)

    def user_can_authenticate(self, user):
        return super().user_can_authenticate(user) and not user.is_suspended

    def get_user(self, user_id):
        user = super().get_user(user_id)
        return user if user and self.user_can_authenticate(user) else None

    def has_perm(self, user_obj, perm, obj=None):
        if not self.user_can_authenticate(user_obj):
            raise PermissionDenied("Account is disabled.")
        scope = role_scope_permissions(user_obj.role)
        if scope is not None:
            app, _, code = perm.partition(".")
            if app != "accounts" or code not in scope:
                raise PermissionDenied("Permission is outside this role's scope.")
        return super().has_perm(user_obj, perm, obj)
