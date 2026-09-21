from django.shortcuts import render

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


class AdminTabAuthMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        token = get_tab_token_from_request(request)
        if token:
            user = get_user_for_tab_token(token)
            if user is not None:
                request.admin_tab_token = token
                request.user = user
                return self.get_response(request)

        if _is_admin_html_path(request.path, request.method):
            accept = request.headers.get("Accept", "")
            if "text/html" in accept:
                return render(
                    request,
                    "user_management/pages/admin_tab_bootstrap.html",
                )

        return self.get_response(request)
