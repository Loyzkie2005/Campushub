import uuid

from django.contrib.auth.models import AbstractUser, Permission
from django.db import models


class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=20, unique=True, blank=True, null=True)

    class Meta:
        db_table = "campushub_department"

    def __str__(self):
        return self.name


class User(AbstractUser):
    role = models.CharField(
        max_length=100,
        default="User",
    )
    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="users",
    )
    contact_number = models.CharField(max_length=30, blank=True, default="")
    is_suspended = models.BooleanField(default=False)

    class Meta:
        db_table = "campushub_accounts_user"

    def __str__(self):
        return self.username


class Role(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    role_name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    granted_permissions = models.ManyToManyField(
        Permission,
        blank=True,
        related_name="campushub_roles",
    )

    class Meta:
        db_table = "campushub_role"
        ordering = ("role_name",)
        verbose_name = "User Role"
        verbose_name_plural = "User Roles"
        permissions = [
            ("can_browse_products", "Can browse products"),
            ("can_buy_products", "Can buy products"),
            ("can_manage_products", "Can manage products"),
            ("can_approve_products", "Can approve products"),
            ("can_manage_orders", "Can manage orders"),
            ("can_manage_sellers", "Can manage seller access"),
            ("can_view_marketplace_reports", "Can view marketplace reports"),
            ("can_browse_facilities", "Can browse facilities"),
            ("can_book_facilities", "Can book facilities"),
            ("can_manage_facilities", "Can manage facilities"),
            ("can_manage_bookings", "Can manage facility bookings"),
            ("can_approve_bookings", "Can approve or reject facility bookings"),
            ("can_manage_schedules", "Can manage facility calendars and schedules"),
            ("can_record_facility_payment", "Can record facility payments and official receipts"),
            ("can_view_facility_reports", "Can view facility reports"),
            ("can_view_users", "Can view users"),
            ("can_manage_admin_accounts", "Can manage administrator accounts"),
            ("can_manage_roles_permissions", "Can manage roles and permissions"),
            ("can_view_user_monitoring", "Can view user monitoring"),
            ("can_view_marketplace_analytics", "Can view marketplace analytics"),
            ("can_view_facility_analytics", "Can view facility analytics"),
            ("can_view_reports", "Can view reports"),
            ("can_generate_reports", "Can generate reports"),
            ("can_access_messages", "Can access messages"),
            ("can_access_notifications", "Can access notifications"),
            ("can_manage_settings", "Can manage system settings"),
            ("can_export_marketplace_data", "Can export marketplace data"),
            ("can_export_facility_data", "Can export facility data"),
            ("can_system_backup", "Can create and download system backups"),
            ("can_restore_system_backup", "Can restore system backups"),
            ("can_backup_restore", "Can back up and restore CampusHub data"),
        ]

    def __str__(self):
        return self.role_name


class AdminTabToken(models.Model):
    key = models.CharField(max_length=64, unique=True, db_index=True)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="admin_tab_tokens",
    )
    remember_me = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()

    class Meta:
        db_table = "campushub_admin_tab_token"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.user.username} ({self.key[:8]}...)"


class AccountActivity(models.Model):
    SOURCE_ADMIN = "admin"
    SOURCE_MOBILE = "mobile"
    SOURCE_UNKNOWN = "unknown"
    SOURCE_CHOICES = (
        (SOURCE_ADMIN, "Admin"),
        (SOURCE_MOBILE, "Mobile"),
        (SOURCE_UNKNOWN, "Unknown"),
    )

    RESULT_SUCCESS = "success"
    RESULT_FAILED = "failed"
    RESULT_CHOICES = (
        (RESULT_SUCCESS, "Success"),
        (RESULT_FAILED, "Failed"),
    )

    account_source = models.CharField(max_length=12, choices=SOURCE_CHOICES)
    account_id = models.PositiveBigIntegerField(null=True, blank=True)
    account_ref = models.CharField(max_length=40, blank=True, db_index=True)
    username = models.CharField(max_length=150, blank=True)
    full_name = models.CharField(max_length=220, blank=True)
    email = models.CharField(max_length=254, blank=True)
    account_type = models.CharField(max_length=24, blank=True)
    role = models.CharField(max_length=100, blank=True)
    activity_type = models.CharField(max_length=40, db_index=True)
    activity = models.CharField(max_length=180)
    module = models.CharField(max_length=80, default="Authentication")
    result = models.CharField(max_length=12, choices=RESULT_CHOICES)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    session_identifier = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "campushub_account_activity"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=("account_source", "account_id", "-created_at"), name="acct_activity_user_idx"),
            models.Index(fields=("activity_type", "result", "-created_at"), name="acct_activity_auth_idx"),
        ]

    def __str__(self):
        return f"{self.username or 'Unknown'}: {self.activity}"
