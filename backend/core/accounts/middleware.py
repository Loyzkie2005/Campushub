from django.shortcuts import redirect, render
from django.contrib.auth.models import AnonymousUser

from .admin_tab_auth import get_tab_token_from_request, get_user_for_tab_token


def _is_admin_html_path(path, method):
    if method != "GET":
        return False
    if path in ("/", "/admin-logout/"):
        return False
    if path.startswith("/api/") or path.startswith("/static/") or path.startswith("/media/"):
        return False
    if path.startswith("/admin/"):
        return False
    return path.startswith("/admin")


def _should_disable_browser_cache(path, method):
    if path in ("/", "/admin-logout/", "/api/admin/session/"):
        return True
    return _is_admin_html_path(path, method)


def _apply_no_store_headers(response):
    response["Cache-Control"] = "private, no-store, no-cache, must-revalidate, max-age=0"
    response["Pragma"] = "no-cache"
    response["Expires"] = "0"
    return response


class AdminTabAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(request.user, "is_suspended", False):
            request.user = AnonymousUser()
        token = get_tab_token_from_request(request)
        if token:
            user = get_user_for_tab_token(token)
            if user is not None:
                request.admin_tab_token = token
                request.user = user
                response = self.get_response(request)
                if _should_disable_browser_cache(request.path, request.method):
                    return _apply_no_store_headers(response)
                return response

            request.user = AnonymousUser()
            request._cached_user = request.user
            if _is_admin_html_path(request.path, request.method):
                return _apply_no_store_headers(redirect("admin_login_page"))

        if _is_admin_html_path(request.path, request.method):
            accept = request.headers.get("Accept", "")
            if "text/html" in accept and not getattr(request.user, "is_authenticated", False):
                return _apply_no_store_headers(
                    render(
                        request,
                        "user_management/pages/admin_tab_bootstrap.html",
                    )
                )

        response = self.get_response(request)
        if _should_disable_browser_cache(request.path, request.method):
            return _apply_no_store_headers(response)
        return response
