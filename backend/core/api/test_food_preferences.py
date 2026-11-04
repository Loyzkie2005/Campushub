import json
from django.db import connection
from django.test import TestCase
from api.models import CampusHubUser, MobileFoodPreference
from api.food_preferences import FOOD_ORDER
from modules.messages.auth import mobile_chat_token


class FoodPreferenceTests(TestCase):
    @classmethod
    def setUpClass(cls):
        from django.apps import apps
        tables = set(connection.introspection.table_names())
        with connection.schema_editor() as editor:
            # Legacy unmanaged relationships are needed by normal user deletion too.
            for model in apps.get_app_config('api').get_models():
                if not model._meta.managed and model._meta.db_table not in tables:
                    editor.create_model(model)
                    tables.add(model._meta.db_table)
        super().setUpClass()

    def setUp(self):
        self.owner = CampusHubUser.objects.create(username='preference-owner', email='preferences@example.test',
            first_name='Preference', last_name='Owner', password_hash='unused', user_type='guest', profile_completed=True)
        self.other = CampusHubUser.objects.create(username='preference-other', email='other-pref@example.test',
            first_name='Other', last_name='Owner', password_hash='unused', profile_completed=True)
        self.headers = {'HTTP_AUTHORIZATION': 'Bearer ' + mobile_chat_token(self.owner)}
        self.url = '/api/mobile/profile/preferences/'

    def post(self, data, url=None):
        return self.client.post(url or self.url, json.dumps(data), content_type='application/json', **self.headers)

    def test_authentication_and_incomplete_profile(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.owner.profile_completed = False
        self.owner.save()
        self.assertEqual(self.client.get(self.url, **self.headers).status_code, 409)
        self.assertFalse(MobileFoodPreference.objects.exists())

    def test_legacy_returning_user_get_is_read_only_and_does_not_start_onboarding(self):
        response = self.client.get(self.url, **self.headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual([item['id'] for item in response.json()['categories']], list(FOOD_ORDER))
        self.assertEqual(response.json()['user']['onboarding_stage'], 'complete')
        self.assertFalse(MobileFoodPreference.objects.exists())

    def test_all_six_selections_are_persisted_for_authenticated_owner(self):
        response = self.post({'action': 'save', 'category_ids': list(FOOD_ORDER)})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['preferred_category_ids'], list(FOOD_ORDER))
        self.assertEqual(MobileFoodPreference.objects.get(user=self.owner).category_ids, list(FOOD_ORDER))
        self.assertFalse(MobileFoodPreference.objects.filter(user=self.other).exists())
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.role, 'User')
        self.assertEqual(self.owner.user_type, 'guest')

    def test_invalid_categories_and_owner_forgery_are_rejected_without_writes(self):
        for data in ({'action': 'save', 'category_ids': ['Electronics']},
                {'action': 'save', 'category_ids': [1]}, {'action': 'save', 'category_ids': 'Snacks'},
                {'action': 'save', 'category_ids': ['Snacks'], 'user_id': self.other.pk}, [], None):
            with self.subTest(data=data):
                self.assertEqual(self.post(data).status_code, 400)
        self.assertFalse(MobileFoodPreference.objects.exists())

    def test_optional_empty_selections_and_duplicates(self):
        self.assertEqual(self.post({'action': 'save', 'category_ids': ['Snacks', 'Snacks']}).status_code, 200)
        self.assertEqual(MobileFoodPreference.objects.get(user=self.owner).category_ids, ['Snacks'])
        self.assertEqual(self.post({'action': 'save', 'category_ids': []}).status_code, 200)
        self.assertEqual(MobileFoodPreference.objects.get(user=self.owner).category_ids, [])

    def test_first_profile_completion_preferences_welcome_and_home(self):
        self.owner.profile_completed = False
        self.owner.save()
        response = self.post({'user_type': 'guest', 'contact_number': '09171234567'}, '/api/mobile/profile/complete/')
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(response.json()['user']['onboarding_stage'], 'preferences')
        self.assertEqual(self.post({'action': 'finish'}).status_code, 409)
        self.assertEqual(self.post({'action': 'save', 'category_ids': ['Breakfast']}).json()['user']['onboarding_stage'], 'welcome')
        self.assertEqual(self.post({'action': 'finish'}).json()['user']['onboarding_stage'], 'complete')
        self.assertEqual(self.post({'action': 'finish'}).status_code, 200)
        response = self.post({'user_type': 'guest', 'contact_number': '09171234567'}, '/api/mobile/profile/complete/')
        self.assertEqual(response.json()['user']['onboarding_stage'], 'complete')

    def test_skip_preserves_saved_preferences_and_edit_does_not_restart_welcome(self):
        MobileFoodPreference.objects.create(user=self.owner, category_ids=['Snacks'], onboarding_stage='preferences')
        response = self.post({'action': 'skip'})
        self.assertEqual(response.json()['user']['preferred_category_ids'], ['Snacks'])
        self.assertEqual(response.json()['user']['onboarding_stage'], 'welcome')
        self.post({'action': 'finish'})
        response = self.post({'action': 'save', 'category_ids': ['Beverages']})
        self.assertEqual(response.json()['user']['onboarding_stage'], 'complete')

    def test_disabled_accounts_and_other_methods_are_denied(self):
        self.assertEqual(self.client.delete(self.url, **self.headers).status_code, 405)
        self.owner.is_suspended = True
        self.owner.save()
        self.assertEqual(self.client.get(self.url, **self.headers).status_code, 403)

    def test_existing_profile_edit_does_not_enrol_returning_user(self):
        response = self.post({'user_type': 'guest', 'contact_number': '09171234567'}, '/api/mobile/profile/complete/')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()['user']['onboarding_stage'], 'complete')
        self.assertFalse(MobileFoodPreference.objects.exists())

    def test_login_resumes_saved_stage_and_finishes_without_reprompt(self):
        from django.contrib.auth.hashers import make_password
        self.owner.password_hash = make_password('Isolated-login-123!')
        self.owner.save()
        MobileFoodPreference.objects.create(user=self.owner, onboarding_stage='welcome')
        def login():
            return self.client.post('/api/mobile/login/', json.dumps({'student_id_or_email': self.owner.username,
                'password': 'Isolated-login-123!'}), content_type='application/json')
        self.assertEqual(login().json()['user']['onboarding_stage'], 'welcome')
        self.post({'action': 'finish'})
        self.assertEqual(login().json()['user']['onboarding_stage'], 'complete')

    def test_normal_account_removal_cascades_only_its_own_optional_preferences(self):
        MobileFoodPreference.objects.create(user=self.owner)
        MobileFoodPreference.objects.create(user=self.other)
        self.owner.delete()
        self.assertEqual(MobileFoodPreference.objects.count(), 1)
        self.assertTrue(MobileFoodPreference.objects.filter(user=self.other).exists())
