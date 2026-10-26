"""Preview performance boundaries; no live records or real converter required."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Event
from unittest.mock import patch
import uuid

from django.core.cache import cache
from django.conf import settings
from django.test import SimpleTestCase

from .services import job_order_docx as document
from .services.booking_slip_pdf import BookingSlipPDFError


class JobOrderPreviewTests(SimpleTestCase):
    def setUp(self):
        storage = TemporaryDirectory(prefix='campushub-qa-prepared-documents-')
        self.addCleanup(storage.cleanup)
        settings = self.settings(CACHES={'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'job-preview-test-' + uuid.uuid4().hex,
        }}, JOB_ORDER_PDF_CACHE_DIR=storage.name)
        settings.enable()
        self.addCleanup(settings.disable)
        profile = TemporaryDirectory(prefix='campushub-qa-job-profile-')
        self.addCleanup(profile.cleanup)
        self.profile = self.enterContext(patch.object(document, 'office_profile', return_value=profile))
        self.enterContext(patch.object(document, 'office_binary', return_value='test-office'))
        self.data = {
            'number': 'TEST-JO-1', 'date': 'October 17, 2026',
            'client': {'name': 'Test Client', 'address': '', 'phone': '', 'email': ''},
            'gender_choices': [], 'service_choices': [], 'legacy_gender': '',
            'turnaround_time': '', 'service_other': '', 'specifics': 'Recorded test request',
            'items': '', 'received_at': '', 'required_at': '',
        }

    @staticmethod
    def converted(command, **options):
        Path(command[-1]).with_suffix('.pdf').write_bytes(b'%PDF-test-output')

    def test_unchanged_document_reuses_pdf_and_changed_fields_convert_again(self):
        with patch.object(document.subprocess, 'run', side_effect=self.converted) as convert:
            with patch.object(cache, 'set', wraps=cache.set) as save:
                first = document.job_order_pdf(self.data)
                self.assertEqual(document.job_order_pdf(self.data), first)
                self.assertEqual(convert.call_count, 1)
                self.assertEqual(save.call_args.kwargs['timeout'], 3600)
            document.job_order_pdf({**self.data, 'items': 'New saved item'})
            self.assertEqual(convert.call_count, 2)
            # Each conversion uses a fresh document folder, but the same private profile.
            commands = [call.args[0] for call in convert.call_args_list]
            self.assertEqual(commands[0][1], commands[1][1])
            self.assertNotEqual(commands[0][-1], commands[1][-1])
            self.assertIn('--norestore', commands[0])

    def test_template_content_change_invalidates_cached_pdf(self):
        original = document.job_order_docx(self.data)
        with patch.object(document.subprocess, 'run', side_effect=self.converted) as convert:
            document.job_order_pdf(self.data)
            with patch.object(document, 'job_order_docx', return_value=original + b'changed-template'):
                document.job_order_pdf(self.data)
            self.assertEqual(convert.call_count, 2)

    def test_prepared_pdf_survives_memory_cache_reset_without_reconverting(self):
        with patch.object(document.subprocess, 'run', side_effect=self.converted) as convert:
            first = document.job_order_pdf(self.data)
            cache.clear()  # A restarted worker has no in-memory results.
            self.assertEqual(document.job_order_pdf(self.data), first)
            self.assertEqual(convert.call_count, 1)
            document.job_order_pdf({**self.data, 'items': 'Changed after restart'})
            self.assertEqual(convert.call_count, 2)

    def test_unwritable_persistent_cache_does_not_prevent_document(self):
        with patch.object(document, 'prepared_documents', side_effect=PermissionError):
            with patch.object(document.subprocess, 'run', side_effect=self.converted) as convert:
                self.assertTrue(document.job_order_pdf(self.data).startswith(b'%PDF-'))
                document.job_order_pdf(self.data)
                self.assertEqual(convert.call_count, 1)

    def test_optional_cache_setting_can_be_absent_and_pdf_remains_reusable(self):
        with TemporaryDirectory(prefix='campushub-qa-default-job-cache-') as root:
            with self.settings(BASE_DIR=Path(root)):
                del settings.JOB_ORDER_PDF_CACHE_DIR
                self.assertFalse(hasattr(settings, 'JOB_ORDER_PDF_CACHE_DIR'))
                with patch.object(document.subprocess, 'run', side_effect=self.converted) as convert:
                    first = document.job_order_pdf(self.data)
                    cache.clear()
                    self.assertEqual(document.job_order_pdf(self.data), first)
                    self.assertEqual(convert.call_count, 1)
                self.assertTrue((Path(root) / '.cache' / 'job-order-pdfs').is_dir())

    def test_simultaneous_same_document_converts_once(self):
        started, release = Event(), Event()

        def blocked_conversion(command, **options):
            started.set()
            self.assertTrue(release.wait(5))
            self.converted(command, **options)

        with patch.object(document.subprocess, 'run', side_effect=blocked_conversion) as convert:
            with ThreadPoolExecutor(max_workers=2) as workers:
                first = workers.submit(document.job_order_pdf, self.data)
                self.assertTrue(started.wait(5))
                second = workers.submit(document.job_order_pdf, self.data)
                release.set()
                self.assertEqual(first.result(timeout=5), second.result(timeout=5))
                self.assertEqual(convert.call_count, 1)

    def test_failed_conversion_is_not_cached_and_lock_allows_retry(self):
        def invalid(command, **options):
            Path(command[-1]).with_suffix('.pdf').write_bytes(b'not-a-pdf')

        with patch.object(document.subprocess, 'run', side_effect=invalid):
            with self.assertRaises(BookingSlipPDFError):
                document.job_order_pdf(self.data)
        with patch.object(document.subprocess, 'run', side_effect=self.converted) as convert:
            self.assertTrue(document.job_order_pdf(self.data).startswith(b'%PDF-'))
            self.assertEqual(convert.call_count, 1)
