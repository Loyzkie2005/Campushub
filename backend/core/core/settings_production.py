"""Kamatera settings, selected explicitly with DJANGO_SETTINGS_MODULE.

Development settings remain in core.settings; secrets come from the service
environment rather than the source tree or the PC's SSH-tunnel configuration.
"""

from urllib.parse import urlsplit

from .settings import *  # noqa: F403


def _required(name):
    value = os.environ.get(name, '').strip()
    if not value:
        raise ImproperlyConfigured(f'{name} is required for production.')
    return value


_public_url = urlsplit(_required('CAMPUSHUB_PUBLIC_BASE_URL'))
if (_public_url.scheme != 'https' or not _public_url.hostname
        or _public_url.username or _public_url.password
        or _public_url.path not in ('', '/') or _public_url.query or _public_url.fragment):
    raise ImproperlyConfigured('CAMPUSHUB_PUBLIC_BASE_URL must be an HTTPS origin.')

SECRET_KEY = _required('DJANGO_SECRET_KEY')
CHAT_JWT_SECRET = _required('CHAT_JWT_SECRET')
if len(SECRET_KEY) < 50 or len(CHAT_JWT_SECRET) < 32:
    raise ImproperlyConfigured('Production secret keys are too short.')

DEBUG = False
ROOT_URLCONF = 'core.urls_production'
CAMPUSHUB_PUBLIC_BASE_URL = f'https://{_public_url.netloc}'
ALLOWED_HOSTS = [_public_url.hostname]
CSRF_TRUSTED_ORIGINS = [CAMPUSHUB_PUBLIC_BASE_URL]
CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [CAMPUSHUB_PUBLIC_BASE_URL]
USE_X_FORWARDED_HOST = False
USE_X_FORWARDED_PORT = False
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 3600
SECURE_HSTS_INCLUDE_SUBDOMAINS = False
SECURE_HSTS_PRELOAD = False

_shared_root = Path(os.environ.get('CAMPUSHUB_SHARED_ROOT', '/srv/campushub/shared'))
STATIC_ROOT = _shared_root / 'static'
MEDIA_ROOT = _shared_root / 'media'
CHAT_SERVICE_HTTP_URL = CAMPUSHUB_PUBLIC_BASE_URL + '/chat'
CHAT_SERVICE_WS_URL = 'wss://' + _public_url.netloc + '/chat/ws'

# Configure these privately when email recovery is enabled; no local file needed.
CAMPUSHUB_GMAIL_USER = os.environ.get('CAMPUSHUB_GMAIL_USER', '')
CAMPUSHUB_GMAIL_APP_PASSWORD = os.environ.get('CAMPUSHUB_GMAIL_APP_PASSWORD', '')
EMAIL_HOST_USER = CAMPUSHUB_GMAIL_USER
EMAIL_HOST_PASSWORD = CAMPUSHUB_GMAIL_APP_PASSWORD
DEFAULT_FROM_EMAIL = CAMPUSHUB_GMAIL_USER or f'noreply@{_public_url.hostname}'
