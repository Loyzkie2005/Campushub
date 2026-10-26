from types import SimpleNamespace

import jwt
from django.test import RequestFactory, SimpleTestCase, override_settings

from .auth import admin_chat_token, mobile_chat_token
from .views import _chat_service_config


class ChatServiceConfigTests(SimpleTestCase):
    @override_settings(
        ALLOWED_HOSTS=['campushub.example'],
        CHAT_SERVICE_HTTP_URL='https://campushub.example/chat',
        CHAT_SERVICE_WS_URL='wss://campushub.example/chat/ws',
    )
    def test_public_proxy_urls_keep_https_and_path(self):
        request = RequestFactory().get('/', HTTP_HOST='campushub.example', secure=True)
        self.assertEqual(_chat_service_config(request), {
            'http_url': 'https://campushub.example/chat',
            'ws_url': 'wss://campushub.example/chat/ws',
        })

    @override_settings(
        ALLOWED_HOSTS=['192.168.1.20'],
        CHAT_SERVICE_HTTP_URL='http://127.0.0.1:8001',
        CHAT_SERVICE_WS_URL='ws://127.0.0.1:8001/ws',
    )
    def test_local_development_still_rewrites_for_another_lan_device(self):
        request = RequestFactory().get('/', HTTP_HOST='192.168.1.20:8000')
        self.assertEqual(_chat_service_config(request), {
            'http_url': 'http://192.168.1.20:8001',
            'ws_url': 'ws://192.168.1.20:8001/ws',
        })

    @override_settings(
        ALLOWED_HOSTS=['localhost'],
        CHAT_SERVICE_HTTP_URL='http://127.0.0.1:8001',
        CHAT_SERVICE_WS_URL='ws://127.0.0.1:8001/ws',
    )
    def test_same_pc_keeps_loopback_urls(self):
        request = RequestFactory().get('/', HTTP_HOST='localhost:8000')
        self.assertEqual(_chat_service_config(request)['http_url'], 'http://127.0.0.1:8001')


@override_settings(
    CHAT_JWT_SECRET="test-chat-secret-at-least-32-bytes",
    CHAT_JWT_ALGORITHM="HS256",
    CHAT_TOKEN_LIFETIME_SECONDS=300,
)
class ChatTokenTests(SimpleTestCase):
    def _decode(self, token):
        return jwt.decode(
            token,
            "test-chat-secret-at-least-32-bytes",
            algorithms=["HS256"],
            audience="campushub-chat",
            issuer="campushub-django",
        )

    def test_admin_identity_is_namespaced(self):
        user = SimpleNamespace(
            id=7,
            username="admin",
            role="Super Admin",
            get_full_name=lambda: "Campus Admin",
        )
        claims = self._decode(admin_chat_token(user))
        self.assertEqual(claims["sub"], "admin:7")
        self.assertEqual(claims["name"], "Campus Admin")

    def test_mobile_identity_is_namespaced(self):
        user = SimpleNamespace(
            id=7,
            username="student",
            first_name="Campus",
            last_name="Student",
        )
        claims = self._decode(mobile_chat_token(user))
        self.assertEqual(claims["sub"], "mobile:7")
        self.assertEqual(claims["role"], "Student")
