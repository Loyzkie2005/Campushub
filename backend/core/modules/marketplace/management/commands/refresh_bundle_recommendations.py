from django.core.management.base import BaseCommand, CommandError
from django.core.exceptions import PermissionDenied, ValidationError
from accounts.models import User
from modules.marketplace.services.bundle_monitoring import refresh_live


class Command(BaseCommand):
    help = "Persist current live bundle associations; never imports research CSV or changes orders."

    def add_arguments(self, parser):
        parser.add_argument("--actor", required=True, help="Existing authorized Super Admin username")

    def handle(self, *args, **options):
        try:
            actor = User.objects.get(username=options["actor"])
            result = refresh_live(actor)
        except (User.DoesNotExist, PermissionDenied, ValidationError) as exc:
            raise CommandError("Live refresh failed; verify the authorized actor and analysis configuration.") from exc
        self.stdout.write(f"Created {result['created']}; current {result['current']}; eligible orders {result['transactions']}.")
