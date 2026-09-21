from types import SimpleNamespace

import jwt
from django.test import SimpleTestCase, override_settings

from .auth import admin_chat_token, mobile_chat_token


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
