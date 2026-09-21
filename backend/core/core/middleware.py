import ipaddress
from urllib.parse import urlsplit

from django.conf import settings


class DevHotspotCsrfMiddleware:
    """
    Permits requests originating from any private LAN address (RFC 1918),
    mobile Wi-Fi hotspot (Android, iOS, Windows tethering), loopback, or emulator
    when DEBUG is True.

    This prevents '403 Forbidden: CSRF origin checking failed' errors when
    switching between Wi-Fi networks, mobile hotspots, or connecting from mobile
    devices across the local network during development.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, "DEBUG", False):
            origin = request.META.get("HTTP_ORIGIN")
            if origin:
                try:
                    parsed = urlsplit(origin)
                    hostname = parsed.hostname
                    if hostname:
                        is_trusted = False
                        if hostname in ("localhost", "127.0.0.1", "0.0.0.0", "testserver"):
                            is_trusted = True
                        else:
                            try:
                                ip = ipaddress.ip_address(hostname)
                                if ip.is_private or ip.is_loopback:
                                    is_trusted = True
                            except ValueError:
                                pass

                        if is_trusted:
                            request._dont_enforce_csrf_checks = True
                except Exception:
                    pass

        return self.get_response(request)
