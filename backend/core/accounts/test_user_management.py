"""Regression checks use isolated database records, never live sample accounts."""
import json
import os
from datetime import timedelta
from pathlib import Path

from django.contrib.auth import authenticate
from django.contrib.auth.hashers import check_password, make_password
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from modules.messages.auth import mobile_chat_token
from django.test.utils import CaptureQueriesContext
from django.db import connection

from accounts.models import AccountActivity, Department, ProgramMajor, Role, User
from accounts.role_permissions import set_role_permissions, sync_user_admin_permissions
from accounts.forms import AdminUserCreationForm, AdminUserChangeForm
from accounts.academic import scope_products
from api.models import CampusHubUser, Product, SellerRequest
from modules.messages.auth import mobile_chat_token


@override_settings(CAMPUSHUB_PUBLIC_BASE_URL="https://campushub.example")
class FinalUserManagementTests(TestCase):
    password = 'SecureCampus7!A'

    def setUp(self):
        self.super = User.objects.create_superuser(username='review-super', email='super@example.com', password=self.password, role='Super Admin')
        self.client.force_login(self.super)
        self.bsit = Department.objects.get(code='BSIT')
        self.bfpt = Department.objects.get(code='BFPT')
        self.btled = Department.objects.get(code='BTLED')
        self.he = ProgramMajor.objects.get(program=self.btled, code='HE')
        self.ia = ProgramMajor.objects.get(program=self.btled, code='IA')
        self.student = CampusHubUser.objects.create(first_name='Campus', last_name='Student', username='student-example', email='student@example.com', user_type='student', password_hash=make_password(self.password), department=self.btled, major=self.he)

    def payload(self, **extra):
        data = dict(first_name='Campus', last_name='Administrator', username='review-admin', email='admin@example.com', account_type='admin', role='Marketplace Admin', department=str(self.bsit.pk), password=self.password, confirm_password=self.password, is_active='on')
        data.update(extra)
        return data

    def save(self, **extra):
        return self.client.post(reverse('admin_users_save'), self.payload(**extra), follow=True)

    def action(self, action, **extra):
        return self.client.post(reverse('admin_users_action'), dict(account_ref=f'mobile:{self.student.pk}', action=action, **extra), follow=True)

    def test_global_admin_roles_clear_overposted_program_and_major(self):
        for index, role in enumerate(('Super Admin','Facilities Admin')):
            self.save(role=role, username=f'global-{index}', email=f'global-{index}@example.com', department=str(self.btled.pk), major=str(self.he.pk))
            user = User.objects.get(username=f'global-{index}')
            self.assertIsNone(user.department_id); self.assertIsNone(user.major_id)
            self.assertTrue(user.is_staff); self.assertTrue(check_password(self.password, user.password))

    def test_marketplace_program_and_btled_major_required(self):
        for values in ({'department':''},{'department':str(self.btled.pk)},{'department':str(self.bsit.pk),'major':str(self.he.pk)}):
            self.save(**values)
            self.assertFalse(User.objects.filter(username='review-admin').exists())
        for index, program in enumerate((self.bsit,self.bfpt)):
            self.save(username=f'program-{index}',email=f'program-{index}@example.com',department=str(program.pk))
            self.assertIsNone(User.objects.get(username=f'program-{index}').major_id)
        self.save(department=str(self.btled.pk),major=str(self.he.pk))
        self.assertEqual(User.objects.get(username='review-admin').major,self.he)

    def test_mobile_affiliation_preserved_and_invalid_combinations_rejected(self):
        self.save(account_ref=f'mobile:{self.student.pk}', username=self.student.username, email=self.student.email, account_type='student',role='User',department=str(self.btled.pk),major=str(self.he.pk),password='',confirm_password='')
        self.student.refresh_from_db(); self.assertEqual(self.student.major,self.he)
        response = self.save(account_ref=f'mobile:{self.student.pk}', username=self.student.username,email=self.student.email,account_type='student',role='User',department='',password='',confirm_password='')
        self.assertContains(response,'Select a program.')
        self.student.refresh_from_db(); self.assertEqual(self.student.department,self.btled)

    def test_unassigned_legacy_student_can_be_edited_without_guessing_program(self):
        self.student.department=None; self.student.major=None; self.student.save()
        response = self.save(account_ref=f'mobile:{self.student.pk}', username=self.student.username,email=self.student.email,account_type='student',role='User',department='',password='',confirm_password='')
        self.assertContains(response,'Unassigned')
        self.assertNotContains(response,'Unassigned (legacy record)')
        self.student.refresh_from_db(); self.assertIsNone(self.student.department_id)

    def test_missing_program_display_depends_on_academic_applicability(self):
        from accounts.user_management import build_account_rows
        self.student.department=None; self.student.major=None; self.student.save()
        marketplace=User.objects.create_user(username='missing-marketplace',role='Marketplace Admin')
        facilities=User.objects.create_user(username='no-program-facilities',role='Facilities Admin')
        guest=CampusHubUser.objects.create(username='no-program-guest',email='guest-program@example.com',user_type='guest')
        faculty=CampusHubUser.objects.create(username='no-program-faculty',email='faculty-program@example.com',user_type='faculty')
        affiliated=CampusHubUser.objects.create(username='affiliated-faculty',email='affiliated-program@example.com',user_type='faculty',department=self.bfpt)
        rows={row['ref']:row for row in build_account_rows(self.super)}
        for ref in (f'mobile:{self.student.pk}',f'admin:{marketplace.pk}'):
            row=rows[ref]
            self.assertEqual(row['program_major'],'Unassigned')
            self.assertIn({'label':'Program','value':'Unassigned'},row['detail_fields'])
            self.assertNotIn('Major',[field['label'] for field in row['detail_fields']])
        for ref in (f'admin:{self.super.pk}',f'admin:{facilities.pk}',f'mobile:{guest.pk}',f'mobile:{faculty.pk}'):
            row=rows[ref]
            self.assertEqual(row['program_major'],'—')
            self.assertNotIn('Program',[field['label'] for field in row['detail_fields']])
        self.assertEqual(rows[f'mobile:{affiliated.pk}']['program_major'],'BFPT')
        response=self.client.get(reverse('admin_users_page'))
        self.assertNotContains(response,'Unassigned (legacy record)')

    def test_seller_suspension_preserves_account_and_original_approval(self):
        approved_at=timezone.now()
        application=SellerRequest.objects.create(student_id=self.student.username,full_name='Campus Student',product_type='Supplies',status='approved',reviewed_at=approved_at,reviewed_by=self.super)
        self.action('seller_access',seller_status='suspended')
        application.refresh_from_db(); self.student.refresh_from_db()
        self.assertEqual(application.status,'approved'); self.assertTrue(application.is_suspended); self.assertTrue(self.student.is_active)
        access=self.client.get(reverse('seller_access_status'), HTTP_AUTHORIZATION='Bearer ' + mobile_chat_token(self.student)).json()
        self.assertFalse(access['is_approved_seller']); self.assertEqual(access['status'],'suspended')
        login=self.client.post(reverse('mobile_login'),json.dumps({'student_id_or_email':self.student.username,'password':self.password}),content_type='application/json')
        self.assertEqual(login.status_code,200)
        self.action('seller_access',seller_status='approved',restore='1')
        application.refresh_from_db(); self.assertFalse(application.is_suspended); self.assertEqual(application.reviewed_at,approved_at)

    def test_rejected_is_not_suspended_and_no_application_is_fabricated(self):
        self.action('seller_access',seller_status='approved')
        self.assertFalse(SellerRequest.objects.exists())
        application=SellerRequest.objects.create(student_id=self.student.username,full_name='Campus Student',product_type='Supplies',status='rejected')
        self.action('seller_access',seller_status='suspended')
        application.refresh_from_db(); self.assertFalse(application.is_suspended)
        response=self.client.get(reverse('admin_users_page'),{'seller':'rejected'})
        self.assertEqual(response.context['users'][0]['seller_access_label'],'Rejected')

    def test_filters_are_combined_and_kpis_remain_scope_snapshots(self):
        SellerRequest.objects.create(student_id=self.student.username,full_name='Campus Student',product_type='Supplies',status='pending')
        response=self.client.get(reverse('admin_users_page'),{'department':self.btled.pk,'major':self.he.pk,'seller':'pending','type':'student','status':'active','q':'Campus'})
        self.assertEqual(response.context['paginator'].count,1)
        self.assertEqual(response.context['total_users'],2); self.assertEqual(response.context['pending_sellers'],1)
        self.assertContains(response,'BTLED-HE'); self.assertContains(response,'Clear Filters')
        empty=self.client.get(reverse('admin_users_page'),{'major':self.ia.pk,'department':self.btled.pk})
        self.assertEqual(empty.context['paginator'].count,0)
        cleared=self.client.get(reverse('admin_users_page')); self.assertEqual(cleared.context['paginator'].count,2)

    def test_seller_identity_does_not_mix_mobile_and_web_primary_keys(self):
        SellerRequest.objects.create(user=self.super,student_id=self.student.username,full_name='Different Account',product_type='Supplies',status='pending')
        response=self.client.get(reverse('admin_users_page'))
        row=next(row for row in response.context['users'] if row['source']=='mobile')
        self.assertEqual(row['seller_access'],'not_applied'); self.assertEqual(response.context['pending_sellers'],0)

    def test_read_only_role_has_no_mutation_controls_or_endpoints(self):
        role=Role.objects.create(role_name='Read Only Users'); set_role_permissions(role,['can_view_users'])
        reader=User.objects.create_user(username='reader',role=role.role_name); sync_user_admin_permissions(reader); self.client.force_login(reader)
        response=self.client.get(reverse('admin_users_page'))
        self.assertEqual(response.status_code,200); self.assertNotContains(response,'data-mode="add"'); self.assertNotContains(response,'class="icon-action edit-action')
        self.client.post(reverse('admin_users_save'),self.payload())
        self.assertFalse(User.objects.filter(username='review-admin').exists())
        self.client.post(reverse('admin_users_action'),{'account_ref':f'mobile:{self.student.pk}','action':'deactivate'})
        self.student.refresh_from_db(); self.assertTrue(self.student.is_active)

    def test_builtin_roles_cannot_gain_cross_domain_or_user_admin_permissions(self):
        for role_name, forbidden in (('Facilities Admin','can_manage_products'),('Marketplace Admin','can_manage_bookings')):
            role=Role.objects.get(role_name=role_name)
            set_role_permissions(role,[forbidden,'can_manage_admin_accounts','can_view_user_monitoring'])
            self.assertNotIn(forbidden,role.granted_permissions.values_list('codename',flat=True))
            user=User.objects.create_user(username=role_name.replace(' ','-'),role=role_name)
            sync_user_admin_permissions(user)
            from django.contrib.auth.models import Permission
            user.user_permissions.add(Permission.objects.get(content_type__app_label='accounts',codename=forbidden))
            self.assertFalse(user.has_perm('accounts.'+forbidden))
            self.assertFalse(user.has_perm('accounts.can_manage_admin_accounts'))

    def test_btled_scoping_does_not_expand_when_major_missing(self):
        user=User.objects.create_user(username='scoped',role='Marketplace Admin',department=self.btled,major=self.he)
        ours=Product.objects.create(seller=self.super,name='HE Product',price=10,department=self.btled,major=self.he)
        Product.objects.create(seller=self.super,name='IA Product',price=10,department=self.btled,major=self.ia)
        self.assertEqual(list(scope_products(Product.objects.all(),user)),[ours])
        user.major=None; self.assertFalse(scope_products(Product.objects.all(),user).exists())

    def test_custom_account_manager_cannot_reset_or_edit_super_admin(self):
        role=Role.objects.create(role_name='Account Manager'); set_role_permissions(role,['can_manage_admin_accounts'])
        manager=User.objects.create_user(username='manager',role=role.role_name); sync_user_admin_permissions(manager); self.client.force_login(manager)
        response=self.client.post(reverse('admin_users_action'),{'account_ref':f'admin:{self.super.pk}','action':'reset_password','password':self.password,'confirm_password':self.password})
        self.assertEqual(response.status_code,403)
        response=self.client.post(reverse('admin_users_save'),self.payload(account_ref=f'admin:{self.super.pk}',role='Super Admin'))
        self.super.refresh_from_db(); self.assertEqual(self.super.username,'review-super')

    def test_final_super_admin_and_self_deactivation_are_protected(self):
        response=self.client.post(reverse('admin_users_action'),{'account_ref':f'admin:{self.super.pk}','action':'deactivate'},follow=True)
        self.assertContains(response,'You cannot deactivate')
        self.save(account_ref=f'admin:{self.super.pk}',username=self.super.username,email=self.super.email,role='Marketplace Admin')
        self.super.refresh_from_db(); self.assertTrue(self.super.is_superuser)
        form=AdminUserChangeForm(data={'username':self.super.username,'role':'Facilities Admin','is_active':'on'},instance=self.super)
        self.assertFalse(form.is_valid()); self.assertIn('final active Super Admin',str(form.errors))

    def test_audit_records_changes_without_credentials_and_has_real_recent_activity(self):
        self.save()
        created=User.objects.get(username='review-admin')
        self.assertTrue(AccountActivity.objects.filter(account_ref=f'admin:{created.pk}',activity_type='ADMIN_CREATED').exists())
        from unittest.mock import patch
        self.student.email_verified = True; self.student.save(update_fields=["email_verified"])
        with patch("modules.notifications.services.email_service.send_account_recovery_email", return_value=True):
            self.client.post(reverse("mobile_password_reset"), json.dumps({"email": self.student.email}), content_type="application/json")
        self.student.refresh_from_db(); self.assertTrue(check_password(self.password,self.student.password_hash))
        self.assertNotIn(self.password,str(list(AccountActivity.objects.values())))
        response=self.client.get(reverse('admin_users_page'),{'q':self.student.username})
        self.assertIn('Password Reset Initiated',response.context['users'][0]['activities'][0]['activity'])

    def test_native_admin_creation_reuses_same_scope_validation(self):
        form=AdminUserCreationForm(data=dict(username='native',first_name='Campus',last_name='Admin',email='native@example.com',role='Marketplace Admin',department=self.btled.pk,password1=self.password,password2=self.password,is_active=True))
        self.assertFalse(form.is_valid()); self.assertIn('major',str(form.errors).lower())

    def test_deactivation_blocks_login_but_keeps_user_and_history(self):
        application=SellerRequest.objects.create(student_id=self.student.username,full_name='Campus Student',product_type='Supplies')
        self.action('deactivate'); self.student.refresh_from_db(); application.refresh_from_db()
        self.assertFalse(self.student.is_active); self.assertEqual(application.student_id,self.student.username)
        response=self.client.post(reverse('mobile_login'),json.dumps({'student_id_or_email':self.student.username,'password':self.password}),content_type='application/json')
        self.assertEqual(response.status_code,403)
        self.action('activate'); self.student.refresh_from_db(); self.assertTrue(self.student.is_active)

    def test_disabled_admin_authentication_and_tab_token_are_blocked(self):
        from accounts.admin_tab_auth import create_admin_tab_token,get_user_for_tab_token
        token=create_admin_tab_token(self.super)
        self.super.is_suspended=True; self.super.save(update_fields=['is_suspended'])
        self.assertIsNone(authenticate(username=self.super.username,password=self.password))
        self.assertIsNone(get_user_for_tab_token(token))

    def test_mobile_student_completion_requires_real_program_and_major(self):
        self.student.user_type=''; self.student.department=None; self.student.major=None; self.student.save()
        payload={'user_type':'student','student_id':'2026001234','contact_number':'09171234567'}
        url=reverse('mobile_complete_profile'); headers={'HTTP_AUTHORIZATION':'Bearer '+mobile_chat_token(self.student)}
        response=self.client.post(url,json.dumps(payload),content_type='application/json',**headers); self.assertEqual(response.status_code,400)
        payload['program_id']=self.btled.pk
        response=self.client.post(url,json.dumps(payload),content_type='application/json',**headers); self.assertEqual(response.status_code,400)
        payload['major_id']=self.he.pk
        response=self.client.post(url,json.dumps(payload),content_type='application/json',**headers); self.assertEqual(response.status_code,200)
        self.student.refresh_from_db(); self.assertEqual(self.student.major,self.he)
        self.assertEqual(response.json()['user']['program_major'],'BTLED-HE')

    def test_academic_options_are_database_master_records_only(self):
        data=self.client.get(reverse('mobile_academic_options')).json()
        self.assertEqual({p['code'] for p in data['programs']},{'BSIT','BFPT','BTLED'})
        self.assertEqual({m['code'] for m in data['majors']},{'HE','IA','ICT'})

    def test_seller_approval_preserves_role_and_suspension_blocks_submission(self):
        seller = User.objects.create_user(username='approved-buyer', role='User',
            password=self.password, department=self.bsit)
        application = SellerRequest.objects.create(user=seller, student_id=seller.username,
            full_name='Approved Buyer', product_type='Supplies')
        application.approve(self.super)
        seller.refresh_from_db()
        self.assertEqual(seller.role, 'User')
        self.client.force_login(seller)
        payload = json.dumps({'name':'Allowed listing', 'price':10, 'stock':5})
        url = reverse('seller_submit_product')
        self.assertEqual(self.client.post(url, payload, content_type='application/json').status_code, 201)
        application.is_suspended = True
        application.save(update_fields=['is_suspended'])
        self.assertEqual(self.client.post(url, payload, content_type='application/json').status_code, 403)
        seller.refresh_from_db()
        self.assertTrue(seller.is_active)
        self.assertIsNotNone(authenticate(username=seller.username, password=self.password))
        from modules.marketplace.services.analytics import _approved_seller_ids
        self.assertNotIn(seller.pk, _approved_seller_ids())

    def test_existing_modelbackend_session_cannot_keep_suspended_admin_access(self):
        self.client.force_login(self.super, backend='django.contrib.auth.backends.ModelBackend')
        self.super.is_suspended = True
        self.super.save(update_fields=['is_suspended'])
        self.assertEqual(self.client.get(reverse('admin_users_page')).status_code, 302)

    def test_drawer_fields_follow_real_roles_and_affiliation(self):
        facilities = User.objects.create_user(username='drawer-facilities', role='Facilities Admin')
        bfpt = User.objects.create_user(username='drawer-bfpt', role='Marketplace Admin', department=self.bfpt)
        he = User.objects.create_user(username='drawer-he', role='Marketplace Admin', department=self.btled, major=self.he)
        bsit = CampusHubUser.objects.create(username='drawer-bsit', email='drawer-bsit@example.com', user_type='student', department=self.bsit, role='User', password_hash='unused')
        ia = CampusHubUser.objects.create(username='drawer-ia', email='drawer-ia@example.com', user_type='student', department=self.btled, major=self.ia, role='User', password_hash='unused')
        guest = CampusHubUser.objects.create(username='drawer-guest', email='drawer-guest@example.com', user_type='guest', role='User', password_hash='unused')
        response = self.client.get(reverse('admin_users_page'))
        rows = {row['ref']:row for row in response.context['users']}
        expected = {
            f'admin:{self.super.pk}':['System Scope'],
            f'admin:{facilities.pk}':['Facility Scope'],
            f'admin:{bfpt.pk}':['Program'],
            f'admin:{he.pk}':['Program','Major'],
            f'mobile:{bsit.pk}':['Program','Seller Access'],
            f'mobile:{ia.pk}':['Program','Major','Seller Access'],
            f'mobile:{guest.pk}':[],
        }
        for ref, labels in expected.items():
            self.assertEqual([field['label'] for field in rows[ref]['detail_fields']], labels)
        self.assertEqual(rows[f'admin:{he.pk}']['detail_fields'][1]['value'],self.he.name)
        self.assertEqual(rows[f'admin:{facilities.pk}']['program_major'],'—')
        # Export database-rendered output for reversible browser checks only.
        if os.environ.get('USERS_REVIEW_DIR'):
            Path(os.environ['USERS_REVIEW_DIR'],'drawer.html').write_bytes(response.content)
        SellerRequest.objects.create(student_id=guest.username, status='pending')
        rows = self.client.get(reverse('admin_users_page')).context['users']
        guest_row = next(row for row in rows if row['ref']==f'mobile:{guest.pk}')
        self.assertEqual([field['label'] for field in guest_row['detail_fields']],['Seller Access','Application Status'])

    def test_drawer_updates_after_role_change_and_honest_legacy_major(self):
        facilities = User.objects.create_user(username='changing-facility',email='changing@example.com',role='Facilities Admin')
        edits = dict(account_ref=f'admin:{facilities.pk}',username=facilities.username,email=facilities.email,password='',confirm_password='')
        self.save(**edits,role='Marketplace Admin',department=str(self.btled.pk),major=str(self.he.pk))
        row = next(row for row in self.client.get(reverse('admin_users_page')).context['users'] if row['ref']==edits['account_ref'])
        self.assertEqual([field['label'] for field in row['detail_fields']],['Program','Major'])
        self.save(**edits,role='Facilities Admin',department=str(self.btled.pk),major=str(self.he.pk))
        facilities.refresh_from_db(); self.assertIsNone(facilities.department_id); self.assertIsNone(facilities.major_id)
        row = next(row for row in self.client.get(reverse('admin_users_page')).context['users'] if row['ref']==edits['account_ref'])
        self.assertEqual(row['detail_fields'],[{'label':'Facility Scope','value':'All Facilities'}])
        self.student.major=None; self.student.save(update_fields=['major'])
        row = next(row for row in self.client.get(reverse('admin_users_page')).context['users'] if row['source']=='mobile')
        self.assertEqual(row['detail_fields'][1]['value'],'Unassigned')

    def test_five_newest_events_link_to_exact_account_paginated_history(self):
        ref = f'mobile:{self.student.pk}'
        for number in range(26):
            AccountActivity.objects.create(account_source='mobile',account_id=self.student.pk,account_ref=ref,
                username=self.student.username,activity_type='USER_UPDATED',activity=f'Account event {number}',result='success',
                ip_address=f'192.0.2.{number+1}',user_agent=f'Test agent {number}')
        # Old events with equal timestamps exercise stable PK tie-breaking.
        AccountActivity.objects.filter(account_ref=ref).update(created_at=timezone.now()-timedelta(days=45))
        AccountActivity.objects.create(account_source='admin',account_id=self.super.pk,account_ref=f'admin:{self.super.pk}',
            activity_type='login_success',activity='Unrelated activity',result='success')
        rows = self.client.get(reverse('admin_users_page')).context['users']
        row = next(row for row in rows if row['ref']==ref)
        self.assertEqual([event['activity'] for event in row['activities']],[f'Account event {n}' for n in range(25,20,-1)])
        self.assertTrue(row['has_more_activity']); self.assertIn('account_ref=mobile%3A',row['activity_url'])
        response = self.client.get(row['activity_url'])
        self.assertEqual(response.status_code,200); self.assertEqual(response.context['paginator'].count,1)
        self.assertEqual(response.context['history_page_obj'].paginator.count,26)
        self.assertEqual(len(response.context['users_json'][0]['events']),20)
        self.assertEqual(response.context['users_json'][0]['events'][0]['activity'],'Account event 25')
        self.assertNotContains(response,'Unrelated activity')
        second = self.client.get(reverse('admin_user_monitoring_page'),{'account_ref':ref,'history_page':2})
        self.assertEqual(len(second.context['users_json'][0]['events']),6)
        self.assertEqual(second.context['users_json'][0]['events'][-1]['activity'],'Account event 0')
        self.assertEqual(second.context['users_json'][0]['lastActivity'],'User Updated')
        self.assertEqual(second.context['users_json'][0]['device'],'Unknown')
        self.assertEqual(self.client.get(reverse('admin_user_monitoring_page'),{'account_ref':'mobile:999999999'}).status_code,404)
        self.assertNotIn('password_hash',row)
        if os.environ.get('USERS_REVIEW_DIR'):
            folder=Path(os.environ['USERS_REVIEW_DIR'])
            (folder/'drawer-activity.html').write_bytes(self.client.get(reverse('admin_users_page')).content)
            (folder/'monitor-history.html').write_bytes(response.content)

    def test_activity_link_respects_existing_monitoring_permission(self):
        ref = f'mobile:{self.student.pk}'
        for number in range(6):
            AccountActivity.objects.create(account_source='mobile',account_ref=ref,activity_type='USER_UPDATED',activity=f'Updated {number}',result='success')
        role=Role.objects.create(role_name='Drawer Reader')
        set_role_permissions(role,['can_view_users','can_view_user_monitoring'])
        reader=User.objects.create_user(username='drawer-reader',role=role.role_name)
        sync_user_admin_permissions(reader); self.client.force_login(reader)
        row = next(row for row in self.client.get(reverse('admin_users_page')).context['users'] if row['ref']==ref)
        self.assertTrue(row['has_more_activity']); self.assertEqual(row['activity_url'],'')
        self.assertEqual(self.client.get(reverse('admin_user_monitoring_page'),{'account_ref':ref}).status_code,403)

    def test_page_query_count_does_not_grow_with_rows_and_export_for_browser(self):
        def query_count():
            with CaptureQueriesContext(connection) as queries:
                response=self.client.get(reverse('admin_users_page'))
            return len(queries),response
        count,_=query_count()
        for n in range(8):
            CampusHubUser.objects.create(first_name='Campus',last_name=f'Student {n}',username=f'row-{n}',email=f'row-{n}@example.com',password_hash='unused',user_type='student',department=self.btled,major=self.he)
        self.assertLessEqual(query_count()[0],count+1)
        self.save(role='Facilities Admin')
        SellerRequest.objects.create(student_id=self.student.username,full_name='Campus Student',product_type='Supplies',status='approved')
        if os.environ.get('USERS_REVIEW_DIR'):
            folder=Path(os.environ['USERS_REVIEW_DIR']); folder.mkdir(parents=True,exist_ok=True)
            for name,params in (('users',{}),('empty',{'q':'No Match'}),('btled',{'department':self.btled.pk,'major':self.he.pk})):
                response=self.client.get(reverse('admin_users_page'),params)
                (folder/f'{name}.html').write_bytes(response.content)
