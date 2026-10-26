"""Bound incorrect guesses for the existing mobile recovery code workflow."""
from django.contrib.auth.hashers import check_password
from django.utils import timezone


def verify_reset_code(reset, code):
    if reset is None or reset.used or reset.expires_at <= timezone.now():
        return False
    if reset.attempts >= 5:
        reset.used = True
        reset.save(update_fields=["used"])
        return False
    if isinstance(code, str) and len(code) == 6 and code.isascii() and code.isdigit() and check_password(code, reset.code_hash):
        return True
    reset.attempts += 1
    reset.used = reset.attempts >= 5
    reset.save(update_fields=["attempts", "used"])
    return False
