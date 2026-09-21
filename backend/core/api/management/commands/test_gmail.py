"""Test Gmail: python manage.py test_gmail lesterbulay18@gmail.com"""

from django.core.management.base import BaseCommand

from api.email_service import get_smtp_config, is_gmail_configured, send_password_reset_email


class Command(BaseCommand):
    help = "Send a test password-reset email via Gmail SMTP"

    def add_arguments(self, parser):
        parser.add_argument("to_email", type=str, help="Recipient email address")

    def handle(self, *args, **options):
        to_email = options["to_email"].strip()

        if not is_gmail_configured():
            self.stderr.write(
                self.style.ERROR(
                    "Gmail not configured.\n"
                    "Edit backend/core/core/gmail_local.py\n"
                    "Set CAMPUSHUB_GMAIL_APP_PASSWORD (16 chars from Google App Passwords)"
                )
            )
            return

        config = get_smtp_config()
        self.stdout.write(f"Sender: {config.gmail_user}")
        self.stdout.write(f"Sending test code to: {to_email}")

        try:
            send_password_reset_email(
                to_email=to_email,
                code="123456",
                full_name="Test User",
            )
        except Exception as exc:
            self.stderr.write(self.style.ERROR(f"FAILED: {exc}"))
            return

        self.stdout.write(self.style.SUCCESS("Email sent! Check inbox and spam folder."))
