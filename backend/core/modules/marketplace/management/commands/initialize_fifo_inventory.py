"""Dry-run by default. --apply is a separately approved working-data cutover."""
import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from modules.marketplace.services import fifo


class Command(BaseCommand):
    help = "Preview FIFO opening balances; apply only with explicit cutover approval, verified backup and fingerprint."

    def add_arguments(self, parser):
        parser.add_argument("--apply", action="store_true")
        parser.add_argument("--backup-file")
        parser.add_argument("--expected-fingerprint")

    def handle(self, *args, **options):
        if not options["apply"]:
            self.stdout.write(json.dumps(fifo.reconciliation(), indent=2))
            return
        backup = Path(options["backup_file"] or "")
        if not backup.is_file() or backup.stat().st_size < 100 or not options["expected_fingerprint"]:
            raise CommandError("A verified recoverable backup and current dry-run fingerprint are required.")
        # Backup manifest comes from the separately reviewed backup/restore verification.
        import hashlib
        manifest_path = backup.with_suffix(backup.suffix + ".verified.json")
        try:
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            raise CommandError("Verified backup manifest is missing; cutover blocked.") from exc
        from django.db import connection
        config = connection.settings_dict
        identity = hashlib.sha256(json.dumps({"host": str(config.get("HOST") or "localhost"),
            "port": str(config.get("PORT") or 5432), "name": config["NAME"]}, sort_keys=True).encode()).hexdigest()
        if (manifest.get("database") != connection.settings_dict["NAME"] or
            manifest.get("database_identity") != identity or
            manifest.get("sha256") != hashlib.sha256(backup.read_bytes()).hexdigest() or
            manifest.get("opening_fingerprint") != options["expected_fingerprint"] or
            not manifest.get("restore_verified")):
            raise CommandError("Backup verification does not match this database/file; cutover blocked.")
        try:
            result = fifo.initialize(options["expected_fingerprint"])
        except fifo.FIFOError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(json.dumps(result, indent=2))
