"""Run once, or keep polling the committed outbox in a separate worker terminal."""
import time

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections
from django.utils import timezone

from api.models import ProductApprovalPush
from modules.notifications.services.push_service import dispatch_delivery


class Command(BaseCommand):
    help = "Deliver committed product approval/rejection decisions to their registered mobile sellers."

    def add_arguments(self, parser):
        parser.add_argument("--watch", action="store_true", help="Poll every five seconds until Ctrl+C.")
        parser.add_argument("--limit", type=int, default=100)
        parser.add_argument("--retry-now", action="store_true", help="Reset failed delivery attempts once.")

    def handle(self, *args, **options):
        if not settings.CAMPUSHUB_FCM_ENABLED:
            raise CommandError("Set CAMPUSHUB_FCM_ENABLED=true and configure server credentials first.")
        if not 1 <= options["limit"] <= 500:
            raise CommandError("Limit must be between 1 and 500.")
        if options["retry_now"]:
            ProductApprovalPush.objects.filter(status="failed").update(attempts=0, retry_at=timezone.now())
        try:
            while True:
                close_old_connections()
                ids = list(ProductApprovalPush.objects.filter(status__in=["pending", "failed"],
                    attempts__lt=3, retry_at__lte=timezone.now()).order_by("pk").values_list(
                        "pk", flat=True)[:options["limit"]])
                results = {}
                for delivery_id in ids:
                    result = dispatch_delivery(delivery_id)
                    results[result] = results.get(result, 0) + 1
                if ids or not options["watch"]:
                    self.stdout.write(f"Product review push results: {results}")
                if not options["watch"]:
                    return
                time.sleep(5)
        except KeyboardInterrupt:
            self.stdout.write("Product review push worker stopped.")
