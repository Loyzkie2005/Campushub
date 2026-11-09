# Original location: backend/core/modules/facilities/test_job_order_signatures.py
"""End-to-end signing boundaries with disposable PostgreSQL records only."""
import base64
from datetime import timedelta
from io import BytesIO
import json
from unittest.mock import patch
from zipfile import ZipFile

from PIL import Image, ImageDraw
from django.db import connection
from django.test import Client, TestCase, TransactionTestCase
from django.core.exceptions import ValidationError
from django.utils import timezone
from accounts.models import User, AccountActivity
from accounts.role_permissions import sync_user_admin_permissions
from api.models import Booking, CampusHubUser, Facility, Room, FacilityPayment
from modules.messages.auth import mobile_chat_token
from modules.facilities.services.job_order import job_order_data
from modules.facilities.services.job_order_docx import job_order_docx, NS, TEMPLATE
from modules.facilities.services.job_order_signatures import validated_png


def signature(number=0, blank=False):
    image = Image.new('RGBA', (400, 180), 'white')
    if not blank:
        ImageDraw.Draw(image).line([(20, 100), (70, 20 + number), (110, 130), (280, 50 + number)], fill='navy', width=4)
    stream = BytesIO()
    image.save(stream, 'PNG')
    return 'data:image/png;base64,' + base64.b64encode(stream.getvalue()).decode()


class JobOrderSignatureTests(TestCase):
    @classmethod
    def setUpClass(cls):
        tables = connection.introspection.table_names()
        with connection.schema_editor() as editor:
            for model in (CampusHubUser, Facility, Room, Booking, FacilityPayment):
                if model._meta.db_table not in tables:
                    editor.create_model(model)
        super().setUpClass()

    def setUp(self):
        self.admin = User.objects.create_user(username='signature-aide', first_name='Recorded', last_name='Aide', role='Facilities Admin', is_staff=True)
        self.personnel = User.objects.create_user(username='signature-personnel', role='Facilities Admin', is_staff=True)
        self.manager = User.objects.create_user(username='signature-manager', role='Facilities Admin', is_staff=True)
        for user in (self.admin, self.personnel, self.manager):
            sync_user_admin_permissions(user)
        self.roster = self.settings(JOB_ORDER_SIGNERS={'assisted_by': self.admin.username,
            'verified_by': self.personnel.username, 'approved_by': self.manager.username})
        self.roster.enable(); self.addCleanup(self.roster.disable)
        self.user = CampusHubUser.objects.create(username='signature-client', first_name='Recorded', last_name='Client',
            email='signature@example.test', contact_number='09171234567', password_hash='unused')
        self.facility = Facility.objects.create(id='SIGN-COURT', facility_name='Signature test court', facility_type='covered_court',
            booking_mode='slot', rate=500, price_type='hour', capacity=50, slots='08:00-12:00;13:00-17:00')
        self.client.force_login(self.admin)
        self.booking = self.create_booking()

    def post(self, client, path, body, **headers):
        return client.post(path, json.dumps(body), content_type='application/json', **headers)

    def create_booking(self, offset=7):
        response = self.post(self.client, '/api/bookings/create/', {'facility_id': self.facility.pk, 'type': 'reservation',
            'date': str(timezone.localdate() + timedelta(days=offset)), 'start': '13:00', 'end': '17:00',
            'purpose': 'Isolated signature test', 'attendees': 10, 'client_type': 'existing', 'client_id': self.user.pk})
        self.assertEqual(response.status_code, 201, response.content)
        return Booking.objects.get(pk=response.json()['event']['id'])

    def prefix(self, booking=None):
        return f'/api/bookings/{(booking or self.booking).pk}/job-order/'

    def mobile(self, booking=None):
        booking = booking or self.booking
        browser = Client()
        prefix = f'/api/mobile/bookings/{booking.pk}/job-order/'
        response = self.post(browser, prefix + 'handoff/', {}, HTTP_AUTHORIZATION='Bearer ' + mobile_chat_token(self.user))
        self.assertEqual(response.status_code, 200, response.content)
        grant = response.json()['handoff']
        opened = browser.get(prefix + 'view/', HTTP_X_JOB_ORDER_HANDOFF=grant)
        self.assertEqual(opened.status_code, 200, opened.content[:200])
        return browser, prefix, grant

    def sign(self, section, number=0, actor=None, browser=None, prefix=None):
        if actor:
            self.client.force_login(actor)
        browser = browser or self.client
        prefix = prefix or self.prefix()
        prepared = self.post(browser, prefix + 'sign/', {'intent': 'prepare', 'section': section})
        self.assertEqual(prepared.status_code, 200, prepared.content)
        response = self.post(browser, prefix + 'sign/', {'intent': 'sign', 'section': section,
            'challenge': prepared.json()['challenge'], 'signature': signature(number), 'name': 'Forged signer', 'at': '1900-01-01'})
        self.assertEqual(response.status_code, 200, response.content)
        return prepared.json()['challenge']

    def client_sign(self, number=0):
        browser, prefix, _ = self.mobile()
        challenge = self.sign('filled_out_by', number, browser=browser, prefix=prefix)
        return browser, prefix, challenge

    def test_four_real_signoffs_keep_booking_and_payment_separate(self):
        before = timezone.now()
        self.client_sign()
        self.sign('assisted_by', 1, self.admin)
        self.sign('verified_by', 2, self.personnel)
        self.sign('approved_by', 3, self.manager)
        self.booking.refresh_from_db()
        job = self.booking.mobile_request.details['job_order']
        self.assertEqual(len(job['signatures']), 4)
        self.assertEqual(job['signatures']['filled_out_by']['actor_ref'], f'mobile:{self.user.pk}')
        self.assertEqual(job['signatures']['assisted_by']['name'], 'Recorded Aide')
        self.assertGreaterEqual(timezone.datetime.fromisoformat(job['signatures']['approved_by']['at']), before)
        self.assertEqual(self.booking.status, 'approved')
        self.assertFalse(self.booking.payments.exists())
        self.assertEqual(AccountActivity.objects.filter(activity_type='job_order_signed').count(), 4)
        response = self.client.get(f'/api/bookings/{self.booking.pk}/')
        self.assertEqual(response.json()['job_order_signing']['signed_count'], 4)
        self.assertNotIn('iVBOR', response.content.decode())
        self.assertNotIn('_signing_private', response.content.decode())
        self.assertNotIn('Forged signer', response.content.decode())

    def test_assignment_and_sequence_are_server_enforced(self):
        for section in ('filled_out_by', 'assisted_by', 'verified_by', 'approved_by', [], None):
            response = self.post(self.client, self.prefix() + 'sign/', {'intent': 'prepare', 'section': section})
            self.assertEqual(response.status_code, 403, response.content)
        self.client_sign()
        with self.settings(JOB_ORDER_SIGNERS={}):
            response = self.post(self.client, self.prefix() + 'sign/', {'intent': 'prepare', 'section': 'assisted_by'})
            self.assertEqual(response.status_code, 403)
        self.client.force_login(self.manager)
        response = self.post(self.client, self.prefix() + 'sign/', {'intent': 'prepare', 'section': 'assisted_by'})
        self.assertEqual(response.status_code, 403)

    def test_facilities_admin_signs_only_the_explicitly_assigned_staff_section(self):
        self.client_sign()
        for index, (section, assigned) in enumerate((('assisted_by', self.admin),
                ('verified_by', self.personnel), ('approved_by', self.manager)), start=1):
            with self.subTest(section=section):
                self.client.force_login(assigned)
                status = self.client.get(f'/api/bookings/{self.booking.pk}/').json()['job_order_signing']
                self.assertEqual([row['section'] for row in status['sections'] if row['can_sign']], [section])
                for other in ('filled_out_by', 'assisted_by', 'verified_by', 'approved_by'):
                    if other != section:
                        response = self.post(self.client, self.prefix() + 'sign/',
                            {'intent': 'prepare', 'section': other})
                        self.assertEqual(response.status_code, 403)
                self.sign(section, index, assigned)
                self.booking.refresh_from_db()
                saved = self.booking.mobile_request.details['job_order']['signatures'][section]
                self.assertEqual(saved['actor_ref'], f'admin:{assigned.pk}')
        self.assertEqual(AccountActivity.objects.filter(activity_type='job_order_signed').count(), 4)
        self.assertEqual(self.booking.status, 'approved')
        self.assertFalse(self.booking.payments.exists())

    def test_unassigned_facilities_admin_cannot_act_as_beu_manager_even_when_sequence_ready(self):
        self.client_sign()
        self.sign('assisted_by', 1, self.admin)
        self.sign('verified_by', 2, self.personnel)
        outsider = User.objects.create_user(username='unassigned-facilities-signature-test',
            role='Facilities Admin', is_staff=True)
        sync_user_admin_permissions(outsider)
        self.client.force_login(outsider)
        status = self.client.get(f'/api/bookings/{self.booking.pk}/').json()['job_order_signing']
        self.assertFalse(any(row['can_sign'] for row in status['sections']))
        self.assertIn('not assigned', status['notice'])
        for intent in ('prepare', 'sign'):
            response = self.post(self.client, self.prefix() + 'sign/', {'intent': intent,
                'section': 'approved_by', 'actor_admin_id': self.manager.pk, 'signature': signature(4)})
            self.assertEqual(response.status_code, 403)
        self.booking.refresh_from_db()
        self.assertNotIn('approved_by', self.booking.mobile_request.details['job_order']['signatures'])
        self.assertEqual(AccountActivity.objects.filter(activity_type='job_order_signed').count(), 3)

    def test_facilities_admin_roster_revocation_during_capture_rejects_confirmation(self):
        self.client_sign()
        prepared = self.post(self.client, self.prefix() + 'sign/', {'intent': 'prepare', 'section': 'assisted_by'})
        self.assertEqual(prepared.status_code, 200)
        with self.settings(JOB_ORDER_SIGNERS={}):
            response = self.post(self.client, self.prefix() + 'sign/', {'intent': 'sign',
                'section': 'assisted_by', 'challenge': prepared.json()['challenge'], 'signature': signature(1)})
            self.assertEqual(response.status_code, 403)
        self.booking.refresh_from_db()
        self.assertNotIn('assisted_by', self.booking.mobile_request.details['job_order']['signatures'])
        self.assertEqual(AccountActivity.objects.filter(activity_type='job_order_signed').count(), 1)

    def test_unconfigured_staff_roster_explains_missing_action_and_mobile_client_path(self):
        with self.settings(JOB_ORDER_SIGNERS={}):
            status = self.client.get(f'/api/bookings/{self.booking.pk}/').json()['job_order_signing']
            self.assertIn('have not been assigned', status['notice'])
            self.assertIn('Flutter', status['notice'])
            self.assertFalse(any(row['is_current_signer'] or row['can_sign'] for row in status['sections']))
            denied = self.post(self.client, self.prefix() + 'sign/', {'intent': 'prepare', 'section': 'assisted_by'})
            self.assertEqual(denied.status_code, 403)

    def test_assigned_staff_remain_identified_while_waiting_for_the_client(self):
        status = self.client.get(f'/api/bookings/{self.booking.pk}/').json()['job_order_signing']
        section = next(row for row in status['sections'] if row['section'] == 'assisted_by')
        self.assertTrue(section['is_current_signer'])
        self.assertFalse(section['can_sign'])
        self.assertEqual(section['blocked_reason'], 'Waiting for the Client signature.')
        self.assertIn('Flutter', status['notice'])

    def test_assigned_staff_action_becomes_eligible_after_client_signs(self):
        self.client_sign()
        status = self.client.get(f'/api/bookings/{self.booking.pk}/').json()['job_order_signing']
        section = next(row for row in status['sections'] if row['section'] == 'assisted_by')
        self.assertTrue(section['is_current_signer'])
        self.assertTrue(section['can_sign'])
        self.assertEqual(status['notice'], '')

    def test_mobile_owner_receives_client_action_without_administrator_access(self):
        import re
        browser, prefix, _ = self.mobile()
        response = browser.get(prefix + 'view/')
        match = re.search(r'<script id="beuStandaloneSigningData" type="application/json">(.*?)</script>', response.content.decode(), re.S)
        self.assertIsNotNone(match)
        status = json.loads(match[1])
        self.assertTrue(status['sections'][0]['is_current_signer'])
        self.assertTrue(status['sections'][0]['can_sign'])
        self.assertFalse(any(row['can_sign'] for row in status['sections'][1:]))
        self.assertNotEqual(browser.get(f'/api/bookings/{self.booking.pk}/').status_code, 200)

    def test_missing_client_account_has_an_honest_signing_reason(self):
        Booking.objects.filter(pk=self.booking.pk).update(user=None)
        status = self.client.get(f'/api/bookings/{self.booking.pk}/').json()['job_order_signing']
        self.assertIn('client account must first be linked', status['notice'])
        self.assertFalse(status['sections'][0]['can_sign'])

    def test_terminal_booking_notice_does_not_enable_assigned_staff(self):
        Booking.objects.filter(pk=self.booking.pk).update(status='completed')
        status = self.client.get(f'/api/bookings/{self.booking.pk}/').json()['job_order_signing']
        self.assertIn('read-only', status['notice'])
        self.assertTrue(status['sections'][1]['is_current_signer'])
        self.assertFalse(any(row['can_sign'] for row in status['sections']))

    def test_super_admin_cannot_sign_someone_elses_section(self):
        self.client_sign()
        root = User.objects.create_superuser(username='signature-root', email='root@example.test', password='isolated', role='Super Admin')
        self.client.force_login(root)
        response = self.post(self.client, self.prefix() + 'sign/', {'intent': 'prepare', 'section': 'assisted_by'})
        self.assertEqual(response.status_code, 403)

    def test_roster_cannot_grant_an_administrator_the_client_section(self):
        with self.settings(JOB_ORDER_SIGNERS={'filled_out_by': self.admin.username}):
            response = self.post(self.client, self.prefix() + 'sign/', {'intent': 'prepare', 'section': 'filled_out_by'})
            self.assertEqual(response.status_code, 403)

    def test_empty_invalid_and_oversized_images_are_rejected(self):
        for value in (signature(blank=True), '', None, 'data:image/svg+xml;base64,PHN2Zz4=', 'data:image/png;base64,' + 'x' * 720001):
            with self.subTest(value=str(value)[:40]), self.assertRaises(ValidationError):
                validated_png(value)
        browser, prefix, _ = self.mobile()
        prepared = self.post(browser, prefix + 'sign/', {'intent': 'prepare', 'section': 'filled_out_by'}).json()
        invalid = self.post(browser, prefix + 'sign/', {'intent': 'sign', 'section': 'filled_out_by',
            'challenge': prepared['challenge'], 'signature': signature(blank=True)})
        self.assertEqual(invalid.status_code, 400)
        self.assertFalse(AccountActivity.objects.filter(activity_type='job_order_signed').exists())

    def test_consumed_challenge_cannot_replace_a_signature(self):
        browser, prefix, challenge = self.client_sign()
        response = self.post(browser, prefix + 'sign/', {'intent': 'sign', 'section': 'filled_out_by',
            'challenge': challenge, 'signature': signature(9)})
        self.assertEqual(response.status_code, 403)
        self.assertEqual(AccountActivity.objects.filter(activity_type='job_order_signed').count(), 1)

    def test_signature_image_cannot_be_reused_for_another_booking(self):
        self.client_sign()
        other = self.create_booking(9)
        browser, prefix, _ = self.mobile(other)
        prepared = self.post(browser, prefix + 'sign/', {'intent': 'prepare', 'section': 'filled_out_by'}).json()
        response = self.post(browser, prefix + 'sign/', {'intent': 'sign', 'section': 'filled_out_by',
            'challenge': prepared['challenge'], 'signature': signature()})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(AccountActivity.objects.filter(activity_type='job_order_signed').count(), 1)

    def test_signature_images_and_mobile_documents_remain_private(self):
        browser, prefix, _ = self.client_sign()
        image = browser.get(prefix + 'signatures/filled_out_by/')
        self.assertEqual(image.status_code, 200)
        self.assertEqual(image['Content-Type'], 'image/png')
        self.assertEqual(image['Cache-Control'], 'private, no-store')
        self.assertEqual(Client().get(prefix + 'signatures/filled_out_by/').status_code, 403)
        self.assertEqual(Client().get(self.prefix() + 'signatures/filled_out_by/').status_code, 401)
        self.assertEqual(browser.get(prefix + 'document/?format=docx').status_code, 200)
        self.assertNotEqual(Client().get(prefix + 'document/?format=docx').status_code, 200)

    def test_mobile_handoff_is_single_use_and_never_grants_admin_access(self):
        browser, prefix, grant = self.mobile()
        self.assertTrue(browser.cookies['campushub_job_order']['httponly'])
        self.assertEqual(browser.cookies['campushub_job_order']['samesite'], 'Strict')
        self.assertEqual(browser.cookies['campushub_job_order']['path'], prefix)
        self.assertEqual(Client().get(prefix + 'view/', HTTP_X_JOB_ORDER_HANDOFF=grant).status_code, 403)
        self.assertNotEqual(browser.get(f'/api/bookings/{self.booking.pk}/').status_code, 200)
        with patch('django.core.signing.time.time', return_value=timezone.now().timestamp() + 600):
            self.assertEqual(browser.get(prefix + 'view/').status_code, 403)

    def test_other_mobile_client_cannot_view_or_prepare_this_job_order(self):
        other = CampusHubUser.objects.create(username='signature-other', first_name='Other', last_name='Client',
            email='other-signature@example.test', password_hash='unused')
        response = self.post(Client(), f'/api/mobile/bookings/{self.booking.pk}/job-order/handoff/', {},
                             HTTP_AUTHORIZATION='Bearer ' + mobile_chat_token(other))
        self.assertEqual(response.status_code, 404)

    def test_csrf_and_post_only_requirements_are_preserved(self):
        strict = Client(enforce_csrf_checks=True)
        strict.force_login(self.admin)
        self.assertEqual(self.post(strict, self.prefix() + 'sign/', {'intent': 'prepare', 'section': 'assisted_by'}).status_code, 403)
        self.assertEqual(self.client.get(self.prefix() + 'sign/').status_code, 405)
        browser, prefix, _ = self.mobile()
        strict.cookies = browser.cookies
        self.assertEqual(self.post(strict, prefix + 'sign/', {'intent': 'prepare', 'section': 'filled_out_by'}).status_code, 403)

    def test_signed_docx_has_original_layout_and_deterministic_image_parts(self):
        self.client_sign()
        self.booking.refresh_from_db()
        data = job_order_data(self.booking)
        one = job_order_docx(data)
        self.assertEqual(one, job_order_docx(data))
        from lxml import etree as E
        with ZipFile(BytesIO(one)) as document, ZipFile(TEMPLATE) as original:
            root = E.fromstring(document.read('word/document.xml'))
            cells = root.findall('w:body/w:tbl', NS)[1].findall('w:tr', NS)[1].findall('w:tc', NS)
            self.assertIn('Recorded Client', ''.join(cells[0].xpath('.//w:t/text()', namespaces=NS)))
            self.assertEqual(len(cells[0].findall('.//w:drawing', NS)), 1)
            self.assertFalse(cells[1].findall('.//w:drawing', NS))
            self.assertTrue(document.read('word/media/job-order-signature-filled_out_by.png').startswith(b'\x89PNG'))
            for name in original.namelist():
                if name not in ('word/document.xml', 'word/_rels/document.xml.rels'):
                    self.assertEqual(original.read(name), document.read(name), name)

    def test_all_four_signatures_are_embedded_in_their_original_official_cells(self):
        self.client_sign()
        self.sign('assisted_by', 1, self.admin)
        self.sign('verified_by', 2, self.personnel)
        self.sign('approved_by', 3, self.manager)
        self.booking.refresh_from_db()
        data = job_order_data(self.booking)
        from lxml import etree as E
        with ZipFile(BytesIO(job_order_docx(data))) as document, ZipFile(TEMPLATE) as original:
            root = E.fromstring(document.read('word/document.xml'))
            table = root.findall('w:body/w:tbl', NS)[1]
            cells = table.findall('w:tr', NS)[1].findall('w:tc', NS)
            for index, section in enumerate(('filled_out_by', 'assisted_by', 'verified_by', 'approved_by')):
                from zoneinfo import ZoneInfo
                record = data['signatures'][section]
                self.assertIn(record['name'], ''.join(cells[index].xpath('.//w:t/text()', namespaces=NS)))
                stamp = timezone.datetime.fromisoformat(record['at']).astimezone(ZoneInfo('Asia/Manila')).strftime('%b %d, %Y %I:%M %p')
                self.assertIn(stamp, ''.join(cells[index].xpath('.//w:t/text()', namespaces=NS)))
                self.assertEqual(len(cells[index].findall('.//w:drawing', NS)), 1)
                self.assertIn('word/media/job-order-signature-' + section + '.png', document.namelist())
            template = E.fromstring(original.read('word/document.xml'))
            source_table = template.findall('w:body/w:tbl', NS)[1]
            for index in (0, 2):
                self.assertEqual(table.findall('w:tr', NS)[index].xpath('.//w:t/text()', namespaces=NS),
                    source_table.findall('w:tr', NS)[index].xpath('.//w:t/text()', namespaces=NS))

    def test_narrow_signature_fits_the_official_cell_without_aspect_distortion(self):
        self.client_sign()
        self.booking.refresh_from_db()
        data = job_order_data(self.booking)
        image = Image.new('RGBA', (120, 180), 'white')
        ImageDraw.Draw(image).line([(10, 160), (55, 15), (100, 130)], fill='navy', width=4)
        stream = BytesIO(); image.save(stream, 'PNG')
        data['signatures']['filled_out_by']['attachment'] = {
            'data': base64.b64encode(stream.getvalue()).decode(), 'type': 'image/png'}
        from lxml import etree as E
        with ZipFile(BytesIO(job_order_docx(data))) as document:
            root = E.fromstring(document.read('word/document.xml'))
            cell = root.findall('w:body/w:tbl', NS)[1].findall('w:tr', NS)[1].findall('w:tc', NS)[0]
            extent = cell.find('.//wp:extent', NS)
            cx, cy = int(extent.get('cx')), int(extent.get('cy'))
            self.assertLessEqual(cx, 1120000)
            self.assertLessEqual(cy, 400000)
            self.assertAlmostEqual(cx / cy, 120 / 180, places=5)

    def test_edit_preserves_signed_revision_and_requires_fresh_signatures(self):
        self.client_sign()
        response = self.post(self.client, f'/api/bookings/{self.booking.pk}/update/',
            {'action': 'job_order', 'service_types': ['Facility Rental'], 'specifics': 'Changed approved test document'})
        self.assertEqual(response.status_code, 200, response.content)
        self.booking.refresh_from_db()
        job = self.booking.mobile_request.details['job_order']
        self.assertEqual(job['revision'], 2)
        self.assertNotIn('signatures', job)
        self.assertIn('filled_out_by', job['revisions'][0]['signatures'])
        self.assertNotIn('signed_snapshot', job)

    def test_document_fields_remain_frozen_after_profile_changes(self):
        self.client_sign()
        self.booking.refresh_from_db()
        original = job_order_docx(job_order_data(self.booking))
        self.user.email = 'changed-profile@example.test'; self.user.save(update_fields=['email'])
        self.booking.refresh_from_db()
        self.assertEqual(original, job_order_docx(job_order_data(self.booking)))

    def test_sign_hash_and_saved_snapshot_use_one_template_read(self):
        from modules.facilities.services.job_order_signatures import template_bytes
        browser, prefix, _ = self.mobile()
        prepared = self.post(browser, prefix + 'sign/', {'intent': 'prepare', 'section': 'filled_out_by'}).json()
        with patch('modules.facilities.services.job_order_signatures.template_bytes', wraps=template_bytes) as read:
            response = self.post(browser, prefix + 'sign/', {'intent': 'sign', 'section': 'filled_out_by',
                'challenge': prepared['challenge'], 'signature': signature()})
            self.assertEqual(response.status_code, 200, response.content)
            self.assertEqual(read.call_count, 1)

    def test_signature_changes_invalidate_pdf_cache_while_identical_exports_reuse_it(self):
        from tempfile import TemporaryDirectory
        from modules.facilities.services.job_order_docx import job_order_pdf
        self.client_sign()
        self.booking.refresh_from_db()
        first = job_order_data(self.booking)
        self.sign('assisted_by', 1, self.admin)
        self.booking.refresh_from_db()
        second = job_order_data(self.booking)
        def convert(command, **kwargs):
            from pathlib import Path
            from hashlib import sha256
            directory = Path(command[command.index('--outdir') + 1])
            content = (directory / 'job-order.docx').read_bytes()
            (directory / 'job-order.pdf').write_bytes(b'%PDF-1.4\n' + sha256(content).hexdigest().encode())
        with TemporaryDirectory() as directory, self.settings(JOB_ORDER_PDF_CACHE_DIR=directory,
            CACHES={'default': {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': 'signature-cache-test'}}):
            with patch('modules.facilities.services.job_order_docx.office_binary', return_value='isolated-converter'), \
                    patch('modules.facilities.services.job_order_docx.subprocess.run', side_effect=convert) as conversion:
                old_pdf = job_order_pdf(first)
                self.assertEqual(old_pdf, job_order_pdf(first))
                new_pdf = job_order_pdf(second)
                self.assertNotEqual(old_pdf, new_pdf)
                self.assertEqual(new_pdf, job_order_pdf(second))
                self.assertEqual(conversion.call_count, 2)

    def test_pending_completed_and_cancelled_cannot_be_signed(self):
        for state in ('pending', 'completed', 'cancelled'):
            Booking.objects.filter(pk=self.booking.pk).update(status=state)
            response = self.post(self.client, self.prefix() + 'sign/', {'intent': 'prepare', 'section': 'assisted_by'})
            self.assertEqual(response.status_code, 403)
            mobile = Client().get(f'/api/mobile/bookings/{self.booking.pk}/',
                HTTP_AUTHORIZATION='Bearer ' + mobile_chat_token(self.user))
            self.assertEqual(mobile.status_code, 200)
            self.assertEqual(mobile.json()['booking']['can_view_job_order'], state == 'completed')

    def test_edit_during_capture_invalidates_the_old_challenge(self):
        browser, prefix, _ = self.mobile()
        prepared = self.post(browser, prefix + 'sign/', {'intent': 'prepare', 'section': 'filled_out_by'}).json()
        changed = self.post(self.client, f'/api/bookings/{self.booking.pk}/update/',
            {'action': 'job_order', 'service_types': ['Facility Rental'], 'specifics': 'Changed during capture'})
        self.assertEqual(changed.status_code, 200)
        response = self.post(browser, prefix + 'sign/', {'intent': 'sign', 'section': 'filled_out_by',
            'challenge': prepared['challenge'], 'signature': signature()})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AccountActivity.objects.filter(activity_type='job_order_signed').exists())

    def test_audit_failure_rolls_back_signature_and_preserves_challenge(self):
        browser, prefix, _ = self.mobile()
        prepared = self.post(browser, prefix + 'sign/', {'intent': 'prepare', 'section': 'filled_out_by'}).json()
        with patch('modules.facilities.services.job_order_signatures.log_account_activity', side_effect=RuntimeError('Isolated audit failure')):
            with self.assertRaises(RuntimeError):
                self.post(browser, prefix + 'sign/', {'intent': 'sign', 'section': 'filled_out_by',
                    'challenge': prepared['challenge'], 'signature': signature()})
        self.booking.refresh_from_db()
        self.assertNotIn('signatures', self.booking.mobile_request.details['job_order'])
        retry = self.post(browser, prefix + 'sign/', {'intent': 'sign', 'section': 'filled_out_by',
            'challenge': prepared['challenge'], 'signature': signature()})
        self.assertEqual(retry.status_code, 200)

    def test_expired_challenge_is_rejected_without_a_signature(self):
        from django.core import signing
        from modules.facilities.services.job_order_signatures import SALT
        browser, prefix, _ = self.mobile()
        prepared = self.post(browser, prefix + 'sign/', {'intent': 'prepare', 'section': 'filled_out_by'}).json()
        original = signing.loads
        def expired(value, **kwargs):
            if kwargs.get('salt') == SALT:
                raise signing.SignatureExpired('Isolated expired challenge')
            return original(value, **kwargs)
        with patch('django.core.signing.loads', side_effect=expired):
            response = self.post(browser, prefix + 'sign/', {'intent': 'sign', 'section': 'filled_out_by',
                'challenge': prepared['challenge'], 'signature': signature()})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AccountActivity.objects.filter(activity_type='job_order_signed').exists())


class JobOrderSignatureConcurrencyTests(TransactionTestCase):
    setUp = JobOrderSignatureTests.setUp
    post = JobOrderSignatureTests.post
    create_booking = JobOrderSignatureTests.create_booking
    mobile = JobOrderSignatureTests.mobile

    @classmethod
    def setUpClass(cls):
        tables = connection.introspection.table_names()
        with connection.schema_editor() as editor:
            for model in (CampusHubUser, Facility, Room, Booking, FacilityPayment):
                if model._meta.db_table not in tables:
                    editor.create_model(model)
        super().setUpClass()

    def _fixture_teardown(self):
        from django.core.management import call_command
        assert connection.settings_dict['NAME'].startswith('test_')
        call_command('flush', verbosity=0, interactive=False, database='default', reset_sequences=False,
                     allow_cascade=True, inhibit_post_migrate=False)

    def test_concurrent_confirmations_create_exactly_one_signature_and_audit(self):
        from concurrent.futures import ThreadPoolExecutor
        from copy import deepcopy
        from django.db import connections
        from threading import Barrier
        browser, prefix, _ = self.mobile()
        prepared = self.post(browser, prefix + 'sign/', {'intent': 'prepare', 'section': 'filled_out_by'}).json()
        cookies = deepcopy(browser.cookies)
        barrier = Barrier(2)
        def confirm():
            assert connection.settings_dict['NAME'].startswith('test_')
            client = Client(); client.cookies = deepcopy(cookies)
            barrier.wait(timeout=10)
            try:
                return self.post(client, prefix + 'sign/', {'intent': 'sign', 'section': 'filled_out_by',
                    'challenge': prepared['challenge'], 'signature': signature()}).status_code
            finally:
                connections.close_all()
        with ThreadPoolExecutor(max_workers=2) as pool:
            statuses = sorted(pool.map(lambda _: confirm(), range(2)))
        self.assertEqual(statuses, [200, 403])
        self.assertEqual(AccountActivity.objects.filter(activity_type='job_order_signed').count(), 1)
        self.booking.refresh_from_db()
        self.assertEqual(len(self.booking.mobile_request.details['job_order']['signatures']), 1)
        self.assertFalse(self.booking.payments.exists())
