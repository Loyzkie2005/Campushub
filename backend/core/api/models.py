from decimal import Decimal, InvalidOperation
import uuid

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone


class CampusHubUser(models.Model):
    USER_TYPE_STUDENT = "student"
    USER_TYPE_FACULTY = "faculty"
    USER_TYPE_GUEST = "guest"
    USER_TYPE_CHOICES = (
        (USER_TYPE_STUDENT, "Student"),
        (USER_TYPE_FACULTY, "Faculty"),
        (USER_TYPE_GUEST, "Guest"),
    )

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    username = models.CharField(max_length=50, unique=True)
    email = models.CharField(max_length=150, unique=True)
    password_hash = models.TextField()
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        blank=True,
        default="",
    )
    student_id = models.CharField(
        max_length=50,
        unique=True,
        null=True,
        blank=True,
    )
    institutional_id = models.CharField(max_length=50, blank=True, default="")
    contact_number = models.CharField(max_length=30, blank=True, default="")
    year_section = models.CharField(max_length=120, blank=True, default="")
    profile_photo = models.ImageField(upload_to="profile-photos/", max_length=255, blank=True, default="")
    role = models.CharField(max_length=100, blank=True, default="User")
    department = models.ForeignKey(
        "accounts.Department",
        db_column="department_id",
        db_constraint=False,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="mobile_users",
    )
    major = models.ForeignKey("accounts.ProgramMajor", db_constraint=False, null=True, blank=True, on_delete=models.SET_NULL, related_name="mobile_users")
    is_active = models.BooleanField(default=True)
    is_suspended = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    profile_completed = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "campushub_user"

    def __str__(self):
        return self.username

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def owner_ref(self):
        return f"mobile:{self.pk}"


class ProductQuerySet(models.QuerySet):
    """Bulk quantity writes bypass Product.save and are unsafe after FIFO cutover."""
    def update(self, **kwargs):
        if {"stock", "customization_options", "product_type"}.intersection(kwargs):
            from modules.marketplace.services.fifo import enabled, FIFOError
            if enabled():
                raise FIFOError("Use audited Product.save or inventory services for FIFO stock changes.")
        return super().update(**kwargs)

    def bulk_create(self, objs, *args, **kwargs):
        from modules.marketplace.services.fifo import enabled, FIFOError
        if enabled():
            raise FIFOError("Create products through the audited save workflow while FIFO is active.")
        return super().bulk_create(objs, *args, **kwargs)

    def bulk_update(self, objs, fields, batch_size=None):
        if {"stock", "customization_options", "product_type"}.intersection(fields):
            from modules.marketplace.services.fifo import enabled, FIFOError
            if enabled():
                raise FIFOError("Use audited Product.save or inventory services for FIFO stock changes.")
        return super().bulk_update(objs, fields, batch_size=batch_size)


class Product(models.Model):
    objects = ProductQuerySet.as_manager()
    TYPE_SINGLE = "single"
    TYPE_BUNDLE = "bundle"
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    )

    seller = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="seller_products",
        null=True,
        blank=True,
    )
    mobile_seller = models.ForeignKey(CampusHubUser, on_delete=models.CASCADE,
        null=True, blank=True, db_constraint=False, related_name="seller_products")
    product_code = models.CharField(max_length=13, unique=True, blank=True, null=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=80, blank=True)
    product_type = models.CharField(max_length=12, choices=((TYPE_SINGLE, "Single Product"), (TYPE_BUNDLE, "Combo / Bundle Product")), default=TYPE_SINGLE)
    department = models.ForeignKey("accounts.Department", null=True, blank=True, on_delete=models.SET_NULL, related_name="listed_products")
    major = models.ForeignKey("accounts.ProgramMajor", null=True, blank=True, on_delete=models.SET_NULL, related_name="products")
    tags = models.JSONField(default=list, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
    # Null preserves the configured default on legacy/simple listings.
    # Separately tracked options keep their thresholds in customization_options.
    low_stock_threshold = models.PositiveIntegerField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)
    image_url = models.TextField(blank=True)
    customization_enabled = models.BooleanField(default=False)
    customization_options = models.JSONField(default=list, blank=True)
    approval_status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    is_archived = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_products",
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_products",
    )
    source_recommendation = models.ForeignKey("BundleRecommendation", null=True, blank=True,
        on_delete=models.PROTECT, related_name="created_bundles")

    class Meta:
        db_table = "campushub_product"
        constraints = [models.CheckConstraint(condition=(
            models.Q(seller__isnull=False, mobile_seller__isnull=True) |
            models.Q(seller__isnull=True, mobile_seller__isnull=False)), name="product_one_account_owner")]
        ordering = ("-submitted_at",)
        permissions = (
            ("can_view_seller_products", "Can view seller products"),
            ("can_approve_seller_products", "Can approve seller products"),
        )

    def __str__(self):
        return self.name

    @property
    def owner(self):
        from django.core.exceptions import ValidationError
        owner = self.mobile_seller if self.mobile_seller_id else self.seller
        if owner is None:
            raise ValidationError("The product has no recorded account owner.")
        return owner

    @property
    def owner_key(self):
        return f"mobile:{self.mobile_seller_id}" if self.mobile_seller_id else self.seller_id

    @property
    def owner_ref(self):
        return f"mobile:{self.mobile_seller_id}" if self.mobile_seller_id else f"admin:{self.seller_id}"

    def save(self, *args, **kwargs):
        """Keep SKU identities and actual inventory changes with the same write."""
        from django.db import transaction
        from modules.marketplace.services.inventory_records import sync_inventory_records

        using = kwargs.get("using") or self._state.db or "default"
        fields = kwargs.get("update_fields")
        track = fields is None or bool(set(fields) & {"stock", "customization_options", "product_type"})
        with transaction.atomic(using=using):
            before = None
            if track and self.pk and not self._state.adding:
                before = type(self).objects.using(using).select_for_update().filter(pk=self.pk).values(
                    "stock", "customization_options", "product_type"
                ).first()
            super().save(*args, **kwargs)
            if track:
                sync_inventory_records(self, before=before, using=using)

    def get_customization_json(self):
        import json

        return json.dumps(self.customization_options or [])

    def get_price_bounds(self):
        base_price = self.price or Decimal("0.00")
        if not self.customization_enabled:
            return base_price, base_price

        minimum_extra = Decimal("0.00")
        maximum_extra = Decimal("0.00")
        for group in self.customization_options or []:
            if not isinstance(group, dict):
                continue

            extras = []
            for option in group.get("options") or []:
                if not isinstance(option, dict):
                    continue
                try:
                    extra = Decimal(str(option.get("extra_price") or "0.00"))
                except (InvalidOperation, TypeError, ValueError):
                    extra = Decimal("0.00")
                extras.append(max(extra, Decimal("0.00")))

            if not extras:
                continue
            if group.get("required"):
                minimum_extra += min(extras)
            if group.get("selection") == "multiple":
                maximum_extra += sum(extras, Decimal("0.00"))
            else:
                maximum_extra += max(extras)

        return base_price + minimum_extra, base_price + maximum_extra

    def get_price_display(self):
        minimum, maximum = self.get_price_bounds()
        if minimum == maximum:
            return f"₱{minimum:,.2f}"
        return f"₱{minimum:,.2f} – ₱{maximum:,.2f}"

    def get_image_list(self):
        import json

        raw = (self.image_url or "").strip()
        if not raw:
            return []
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [url for url in parsed if url]
            except json.JSONDecodeError:
                pass
        return [raw]

    def get_images_json(self):
        import json

        return json.dumps(self.get_image_list())

    def get_inventory_status(self):
        from .inventory import get_product_inventory_status

        return get_product_inventory_status(self)

    def get_total_stock(self):
        from .inventory import get_product_total_stock

        return get_product_total_stock(self)

    def get_inventory_status_label(self):
        from .inventory import get_inventory_status_label

        return get_inventory_status_label(self.get_inventory_status())

    def approve(self, user):
        with transaction.atomic():
            current = Product.objects.select_for_update().get(pk=self.pk)
            was_approved = current.approval_status == self.STATUS_APPROVED
            self.approval_status = self.STATUS_APPROVED
            self.approved_by = user
            # Preserve the event timestamp on an idempotent repeat approval.
            self.approved_at = current.approved_at if was_approved else timezone.now()
            self.rejection_reason = ""
            self.save(update_fields=["approval_status", "approved_by", "approved_at",
                                     "rejection_reason", "updated_at"])
            if not was_approved:
                from modules.notifications.services.push_service import queue_product_review
                current.approved_at = self.approved_at
                current.approval_status = self.STATUS_APPROVED
                queue_product_review(current)

    def reject(self, user, reason=""):
        with transaction.atomic():
            current = Product.objects.select_for_update().get(pk=self.pk)
            was_rejected = current.approval_status == self.STATUS_REJECTED
            self.approval_status = self.STATUS_REJECTED
            self.approved_by = user
            self.approved_at = current.approved_at if was_rejected else timezone.now()
            self.rejection_reason = reason
            self.save(update_fields=["approval_status", "approved_by", "approved_at",
                                     "rejection_reason", "updated_at"])
            if not was_rejected:
                from modules.notifications.services.push_service import queue_product_review
                current.approved_at = self.approved_at
                current.approval_status = self.STATUS_REJECTED
                queue_product_review(current)

    def archive(self):
        self.is_archived = True
        self.save(update_fields=["is_archived", "updated_at"])

    def unarchive(self):
        self.is_archived = False
        self.save(update_fields=["is_archived", "updated_at"])


class SellerRequest(models.Model):
    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_NEEDS_REVISION = "needs_revision"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending Review"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_NEEDS_REVISION, "Needs Revision"),
    )

    mobile_user = models.ForeignKey(CampusHubUser, on_delete=models.SET_NULL,
        null=True, blank=True, db_constraint=False, related_name="seller_access_requests")
    application_data = models.JSONField(default=dict, blank=True)
    revision_notes = models.TextField(blank=True)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="seller_access_requests",
    )
    student_id = models.CharField(max_length=50)
    full_name = models.CharField(max_length=150)
    course_section = models.CharField(max_length=120, blank=True)
    contact_number = models.CharField(max_length=40, blank=True)
    product_type = models.CharField(max_length=120)
    message = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_seller_requests",
    )
    reviewed_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)
    is_suspended = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "campushub_seller_request"
        constraints = [models.UniqueConstraint(fields=["mobile_user"],
            condition=models.Q(status__in=["pending", "needs_revision", "approved"]), name="one_active_mobile_seller_request")]
        ordering = ("-created_at",)
        permissions = (
            ("can_view_seller_requests", "Can view seller requests"),
            ("can_approve_seller_requests", "Can approve seller requests"),
        )

    def __str__(self):
        return f"{self.full_name} - {self.product_type}"

    def approve(self, user):
        self.status = self.STATUS_APPROVED
        self.is_suspended = False
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.rejection_reason = ""
        # Seller privilege belongs to this application; approval never replaces
        # the account's existing User / administrator role.
        self.save(update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "is_suspended",
            "updated_at",
        ])

    def reject(self, user, reason=""):
        self.status = self.STATUS_REJECTED
        self.is_suspended = False
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save(update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "is_suspended",
            "updated_at",
        ])

    def request_revision(self, user, notes):
        self.status = self.STATUS_NEEDS_REVISION
        self.revision_notes = notes
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.save(update_fields=["status", "revision_notes", "reviewed_by", "reviewed_at", "updated_at"])


class Facility(models.Model):
    """Maps to the 'campushub_facility' table in PostgreSQL."""

    STATUS_AVAILABLE = "available"
    STATUS_UNAVAILABLE = "unavailable"
    STATUS_RESERVED = "reserved"
    STATUS_OCCUPIED = "occupied"
    STATUS_MAINTENANCE = "maintenance"
    STATUS_INACTIVE = "inactive"

    STATUS_CHOICES = (
        (STATUS_AVAILABLE, "Open for Booking"),
        (STATUS_UNAVAILABLE, "Temporarily Unavailable"),
        (STATUS_MAINTENANCE, "Under Maintenance"),
        (STATUS_INACTIVE, "Inactive"),
    )

    TYPE_COVERED_COURT = "covered_court"
    TYPE_FUNCTION_HALL = "function_hall"
    TYPE_HOSTEL = "hostel"
    TYPE_TRAINING_KITCHEN = "training_kitchen"
    TYPE_FOOD_ANALYSIS = "food_analysis"
    TYPE_LEASE_SPACE = "lease_space"
    TYPE_OTHER = "other"

    TYPE_CHOICES = (
        (TYPE_COVERED_COURT, "Covered Court"),
        (TYPE_FUNCTION_HALL, "Function Hall"),
        (TYPE_HOSTEL, "Hostel / Room Accommodation"),
        (TYPE_TRAINING_KITCHEN, "Training Kitchen / Assessment Center"),
        (TYPE_FOOD_ANALYSIS, "Food Analysis Hub"),
        (TYPE_LEASE_SPACE, "Lease of Space"),
        (TYPE_OTHER, "Other"),
    )

    id = models.CharField(primary_key=True, max_length=30, editable=False)
    facility_name = models.CharField(max_length=150)
    facility_type = models.CharField(
        max_length=40,
        choices=TYPE_CHOICES,
        default=TYPE_OTHER,
        blank=True,
        db_column="facility_type",
    )
    location = models.CharField(max_length=180, blank=True, default="")
    description = models.TextField(blank=True, null=True)
    capacity = models.IntegerField(default=0)
    rate = models.DecimalField(max_digits=10, decimal_places=2, default=0, db_column="rate")
    price_type = models.CharField(max_length=20, default="hour")
    booking_mode = models.CharField(max_length=20, default="room")
    rooms_units = models.IntegerField(blank=True, null=True)
    room_type = models.CharField(max_length=120, blank=True, null=True)
    amenities = models.JSONField(default=list, blank=True)
    slots = models.CharField(max_length=120, blank=True, null=True, db_column="slot_details")
    requirements = models.TextField(blank=True, null=True)
    terms_conditions = models.TextField(blank=True, null=True)
    workflow_config = models.JSONField(default=dict, blank=True)
    image_url = models.TextField(blank=True, null=True)
    availability_status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE, db_column="status"
    )
    is_archived = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        "api.CampusHubUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="created_by",
        related_name="created_facilities",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "campushub_facility"
        ordering = ("-created_at",)

    def __str__(self):
        return self.facility_name

    @property
    def custom_facility_type(self):
        """Reuse the configuration JSON; this is not a second database field."""
        workflow = self.workflow_config if isinstance(self.workflow_config, dict) else {}
        value = workflow.get("custom_facility_type", "")
        return value.strip() if self.facility_type == self.TYPE_OTHER and isinstance(value, str) else ""

    def get_facility_type_display(self):
        """One label resolver shared by catalog, booking APIs and reports."""
        from modules.facilities.services.facility_configuration import FACILITY_TYPE_CONFIG

        return self.custom_facility_type or FACILITY_TYPE_CONFIG.get(self.facility_type, {}).get(
            "label", dict(self.TYPE_CHOICES).get(self.facility_type, "Other")
        )

    def archive(self):
        self.is_archived = True
        self.save(update_fields=["is_archived", "updated_at"])

    def unarchive(self):
        self.is_archived = False
        self.save(update_fields=["is_archived", "updated_at"])

    def get_image_list(self):
        import json

        raw = (self.image_url or "").strip()
        if not raw:
            return []
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    return [url for url in parsed if url]
            except json.JSONDecodeError:
                pass
        return [raw]

    def get_images_json(self):
        import json

        return json.dumps(self.get_image_list())

    def get_first_image_url(self):
        images = self.get_image_list()
        return images[0] if images else ""


class Room(models.Model):
    """Maps to the 'campushub_rooms' table in PostgreSQL."""

    STATUS_AVAILABLE = "available"
    STATUS_OCCUPIED = "occupied"
    STATUS_MAINTENANCE = "maintenance"

    STATUS_CHOICES = (
        (STATUS_AVAILABLE, "Available"),
        (STATUS_OCCUPIED, "Occupied"),
        (STATUS_MAINTENANCE, "Maintenance"),
    )

    id = models.UUIDField(primary_key=True, default=None, editable=False)
    facility = models.ForeignKey(
        Facility,
        on_delete=models.CASCADE,
        db_column="facility_id",
        related_name="rooms",
    )
    room_name = models.CharField(max_length=150, blank=True, null=True)
    room_type = models.CharField(max_length=50, blank=True, null=True)
    descriptions = models.TextField(blank=True, null=True)
    capacity = models.IntegerField(default=0)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_AVAILABLE, db_column="status"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "campushub_rooms"
        ordering = ("room_name",)

    def __str__(self):
        return self.room_name or f"Room in {self.facility}"


class Booking(models.Model):
    """Maps to the 'campushub_booking' table in PostgreSQL."""

    STATUS_PENDING = "pending"
    STATUS_APPROVED = "approved"
    STATUS_REJECTED = "rejected"
    STATUS_CANCELLED = "cancelled"
    STATUS_COMPLETED = "completed"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_COMPLETED, "Completed"),
    )

    id = models.CharField(primary_key=True, max_length=30, editable=False)
    user = models.ForeignKey(
        "api.CampusHubUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="user_id",
        related_name="bookings",
    )
    facility = models.ForeignKey(
        Facility,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="facility_id",
        related_name="bookings",
    )
    room_id = models.UUIDField(blank=True, null=True)
    purpose = models.TextField(blank=True, null=True)
    booking_date = models.DateField(blank=True, null=True)
    start_time = models.TimeField(blank=True, null=True)
    end_time = models.TimeField(blank=True, null=True)
    check_in_date = models.DateField(blank=True, null=True)
    check_out_date = models.DateField(blank=True, null=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    status = models.CharField(
        max_length=30, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "campushub_booking"
        ordering = ("-created_at",)

    def __str__(self):
        return f"Booking {self.id} - {self.status}"


class FacilityBookingRequest(models.Model):
    """Request details/origin and schedule metadata alongside the existing Booking."""

    booking = models.OneToOneField(
        Booking, primary_key=True, on_delete=models.CASCADE,
        related_name="mobile_request", db_constraint=False,
    )
    request_key = models.UUIDField(unique=True)
    details = models.JSONField(default=dict)

    class Meta:
        db_table = "campushub_facility_booking_request"


class FacilityPayment(models.Model):
    """Maps to the 'campushub_facility_payment' table in PostgreSQL."""

    PAYMENT_UNPAID = "unpaid"
    PAYMENT_PAID = "paid"
    PAYMENT_FAILED = "failed"

    PAYMENT_STATUS_CHOICES = (
        (PAYMENT_UNPAID, "Unpaid"),
        (PAYMENT_PAID, "Paid"),
        (PAYMENT_FAILED, "Failed"),
    )

    id = models.CharField(primary_key=True, max_length=30, editable=False)
    booking = models.ForeignKey(
        Booking,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="booking_id",
        related_name="payments",
    )
    paid_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(
        max_length=20, choices=PAYMENT_STATUS_CHOICES, default=PAYMENT_UNPAID
    )
    official_receipt_no = models.CharField(max_length=100, blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "campushub_facility_payment"
        ordering = ("-created_at",)

    def __str__(self):
        return f"Payment {self.id} - {self.payment_status}"


class FacilityFeedback(models.Model):
    """Maps to the 'campushub_facility_feedback' table in PostgreSQL."""

    id = models.CharField(primary_key=True, max_length=30, editable=False)
    facility = models.ForeignKey(
        Facility,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="facility_id",
        related_name="feedbacks",
    )
    user = models.ForeignKey(
        "api.CampusHubUser",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        db_column="user_id",
        related_name="facility_feedbacks",
    )
    rating = models.IntegerField(default=0)
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "campushub_facility_feedback"
        ordering = ("-created_at",)

    def __str__(self):
        return f"Feedback {self.id} - Rating: {self.rating}"


class GmailConfig(models.Model):
    """Gmail SMTP credentials stored in PostgreSQL (no .env required)."""

    gmail_user = models.EmailField(help_text="Gmail address that sends reset emails")
    gmail_app_password = models.CharField(
        max_length=128,
        help_text="Google App Password (16 characters)",
    )
    smtp_host = models.CharField(max_length=120, default="smtp.gmail.com")
    smtp_port = models.PositiveIntegerField(default=587)
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "campushub_gmail_config"
        verbose_name = "Gmail configuration"
        verbose_name_plural = "Gmail configurations"

    def __str__(self):
        return f"{self.gmail_user} ({'active' if self.is_active else 'inactive'})"

    @classmethod
    def get_active(cls):
        return cls.objects.filter(is_active=True).order_by("-updated_at").first()


class PasswordResetCode(models.Model):
    """Stores hashed 6-digit reset codes sent via Gmail."""

    email = models.EmailField(db_index=True)
    account_ref = models.CharField(max_length=40, blank=True, default="", db_index=True)
    purpose = models.CharField(max_length=24, default="password", choices=(("password", "Reset Password"), ("username", "Recover Username"), ("email_verification", "Verify Email")))
    attempts = models.PositiveSmallIntegerField(default=0)
    code_hash = models.CharField(max_length=128)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campushub_password_reset_code"
        ordering = ("-created_at",)

    def __str__(self):
        return f"Reset for {self.email}"


class ProductInteraction(models.Model):
    """User behavior used by the ML recommendation engine."""

    INTERACTION_VIEW = "view"
    INTERACTION_CLICK = "click"
    INTERACTION_PURCHASE = "purchase"

    INTERACTION_CHOICES = (
        (INTERACTION_VIEW, "View"),
        (INTERACTION_CLICK, "Click"),
        (INTERACTION_PURCHASE, "Purchase"),
    )

    user_id = models.IntegerField(db_index=True)
    product = models.ForeignKey(
        Product,
        on_delete=models.CASCADE,
        related_name="interactions",
    )
    interaction_type = models.CharField(
        max_length=20,
        choices=INTERACTION_CHOICES,
        default=INTERACTION_VIEW,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campushub_product_interaction"
        ordering = ("-created_at",)
        indexes = [
            models.Index(fields=["user_id", "interaction_type"]),
        ]


def generate_order_code() -> str:
    """12-char code: year prefix 2026 + 8 uppercase letters (e.g. 2026KTMQXZPL)."""
    import secrets
    import string

    suffix = "".join(secrets.choice(string.ascii_uppercase) for _ in range(8))
    return f"2026{suffix}"


class BundleComponent(models.Model):
    """Recipe references only: inventory remains on the component Product/options."""
    bundle = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="bundle_components")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="used_in_bundles")
    selections = models.JSONField(default=list, blank=True)
    required_quantity = models.PositiveIntegerField()

    class Meta:
        db_table = "campushub_bundle_component"
        ordering = ("pk",)
        constraints = [models.CheckConstraint(condition=models.Q(required_quantity__gte=1), name="bundle_component_quantity_positive")]


class MarketplaceOrder(models.Model):
    STATUS_PENDING = "pending"
    STATUS_PROCESSING = "processing"
    STATUS_READY_FOR_PICKUP = "ready_for_pickup"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    PAYMENT_UNPAID = "unpaid"
    PAYMENT_PAID = "paid"

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_PROCESSING, "Processing"),
        (STATUS_READY_FOR_PICKUP, "Ready for Pickup"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    )

    PAYMENT_STATUS_CHOICES = (
        (PAYMENT_UNPAID, "Unpaid"),
        (PAYMENT_PAID, "Paid"),
    )

    product = models.ForeignKey(
        Product,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="marketplace_orders",
    )
    order_code = models.CharField(max_length=12, unique=True, blank=True, null=True)
    buyer_user_id = models.IntegerField(null=True, blank=True, db_index=True)
    buyer_name = models.CharField(max_length=150, blank=True)
    buyer_email = models.EmailField(blank=True)
    product_name = models.CharField(max_length=150)
    category = models.CharField(max_length=80, blank=True)
    seller_name = models.CharField(max_length=150, blank=True)
    seller_contact = models.CharField(max_length=180, blank=True)
    message_to_seller = models.TextField(blank=True)
    option = models.TextField(blank=True)
    customization = models.JSONField(default=dict, blank=True)
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    image_url = models.TextField(blank=True)
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_PENDING,
    )
    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default=PAYMENT_UNPAID,
    )
    official_receipt_no = models.CharField(max_length=100, blank=True)
    payment_encoded_by = models.CharField(max_length=150, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    pickup_location = models.CharField(max_length=180, blank=True)
    pickup_scheduled_at = models.DateTimeField(null=True, blank=True)
    picked_up_at = models.DateTimeField(null=True, blank=True)
    # Blank means a historical order did not record its fulfillment method.
    fulfillment_method = models.CharField(max_length=20, blank=True, default="",
        choices=(("pickup", "Pickup"), ("seller_delivery", "Seller Delivery")))
    delivery_destination = models.CharField(max_length=500, blank=True)
    delivery_started_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    inventory_deducted = models.BooleanField(default=False)
    inventory_restored = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "campushub_orders"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.product_name} x{self.quantity}"

    def ensure_order_code(self, *, force: bool = False) -> str:
        valid = (
            bool(self.order_code)
            and len(self.order_code) == 12
            and self.order_code.startswith("2026")
        )
        if valid and not force:
            return self.order_code
        for _ in range(20):
            code = generate_order_code()
            qs = MarketplaceOrder.objects.filter(order_code=code)
            if self.pk:
                qs = qs.exclude(pk=self.pk)
            if not qs.exists():
                self.order_code = code
                return code
        self.order_code = generate_order_code()
        return self.order_code

    def save(self, *args, **kwargs):
        # Historical references must survive reads and operational updates unchanged.
        if self._state.adding or not self.order_code:
            self.ensure_order_code()
        super().save(*args, **kwargs)

    def get_customization_json(self):
        import json

        return json.dumps(self.customization or {})


class MarketplaceOrderStatusHistory(models.Model):
    order = models.ForeignKey(
        MarketplaceOrder,
        on_delete=models.CASCADE,
        related_name="status_history",
    )
    previous_status = models.CharField(max_length=20, blank=True)
    new_status = models.CharField(max_length=20)
    changed_by = models.CharField(max_length=150, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campushub_order_status_history"
        ordering = ("-created_at",)


class InventorySKU(models.Model):
    """A persistent stock identity; quantity stays in the existing Product JSON."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="inventory_skus")
    group_name = models.TextField(blank=True, default="")
    variant_name = models.TextField(blank=True, default="")
    prefix = models.CharField(max_length=3, editable=False)
    variant_code = models.CharField(max_length=4, blank=True, default="", editable=False)

    class Meta:
        db_table = "campushub_inventory_sku"
        constraints = [models.UniqueConstraint(fields=["product", "group_name", "variant_name"], name="inventory_sku_product_option_unique")]

    @property
    def code(self):
        parts = [self.prefix]
        if self.variant_code:
            parts.append(self.variant_code)
        parts.append(f"{self.pk:03d}")
        return "-".join(parts)


class InventoryStockMovement(models.Model):
    """Observed changes, never reconstructed opening/restock quantities."""
    KIND_CHOICES = (("opening", "Initial stock"), ("adjustment", "Stock adjustment"), ("receipt", "Stock received"),
                    ("reservation", "Reservation"), ("release", "Reservation released"), ("sale", "Sale"))
    sku = models.ForeignKey(InventorySKU, on_delete=models.CASCADE, related_name="movements")
    order = models.ForeignKey(MarketplaceOrder, null=True, blank=True, on_delete=models.SET_NULL, related_name="inventory_movements")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    quantity_change = models.IntegerField()
    balance = models.CharField(max_length=12, choices=(("available", "Available"), ("on_hand", "On Hand")), default="available")
    available_before = models.PositiveIntegerField(null=True, blank=True)
    available_after = models.PositiveIntegerField(null=True, blank=True)
    actor = models.CharField(max_length=150, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campushub_inventory_stock_movement"
        ordering = ("-created_at", "-pk")
        indexes = [models.Index(fields=["sku", "-created_at"], name="inventory_movement_sku_date")]


class InventoryFIFOControl(models.Model):
    """Explicit cutover marker; creating schema alone never activates FIFO."""
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    active = models.BooleanField(default=False)
    initialized_at = models.DateTimeField(null=True, blank=True)


class InventoryBatch(models.Model):
    sku = models.ForeignKey(InventorySKU, on_delete=models.PROTECT, related_name="batches")
    receipt_movement = models.ForeignKey(InventoryStockMovement, null=True, blank=True, on_delete=models.SET_NULL, related_name="received_batches")
    reference = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    origin = models.CharField(max_length=12, choices=(("receipt", "Stock receipt"), ("opening", "Opening Balance — Historical Receipt Unknown"), ("adjustment", "Stock adjustment")))
    received_at = models.DateTimeField(null=True, blank=True)
    recorded_at = models.DateTimeField(default=timezone.now, editable=False)
    initial_quantity = models.PositiveIntegerField()
    remaining_quantity = models.PositiveIntegerField()
    transaction_reference = models.CharField(max_length=150, blank=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    actor = models.CharField(max_length=150, blank=True)

    class Meta:
        ordering = ("recorded_at", "pk")
        constraints = [models.CheckConstraint(condition=models.Q(initial_quantity__gt=0), name="fifo_batch_initial_positive"),
                       models.CheckConstraint(condition=models.Q(remaining_quantity__lte=models.F("initial_quantity")), name="fifo_batch_balance_bounded")]
        indexes = [models.Index(fields=["sku", "recorded_at"], name="fifo_batch_sku_date")]

    @property
    def code(self):
        return f"BAT-{self.pk:08d}"


class InventoryBatchAllocation(models.Model):
    batch = models.ForeignKey(InventoryBatch, on_delete=models.PROTECT, related_name="allocations")
    movement = models.ForeignKey(InventoryStockMovement, null=True, blank=True, on_delete=models.SET_NULL, related_name="fifo_allocations")
    order = models.ForeignKey(MarketplaceOrder, null=True, blank=True, on_delete=models.SET_NULL, related_name="fifo_allocations")
    order_reference = models.CharField(max_length=30, blank=True)
    quantity = models.PositiveIntegerField()
    state = models.CharField(max_length=12, choices=(("reserved", "Reserved"), ("consumed", "Consumed"), ("released", "Released"), ("adjustment", "Stock adjustment")))
    legacy = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.CheckConstraint(condition=models.Q(quantity__gt=0), name="fifo_allocation_positive")]
        indexes = [models.Index(fields=["order", "state"], name="fifo_order_state")]


class InventoryOperation(models.Model):
    kind = models.CharField(max_length=12)
    key = models.UUIDField()
    fingerprint = models.CharField(max_length=64)
    response = models.JSONField(null=True, blank=True)
    status_code = models.PositiveSmallIntegerField(default=200)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["kind", "key"], name="fifo_operation_unique")]


class BundleRecommendation(models.Model):
    """A persisted live association; research CSV rules never enter this table."""
    product_a = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="recommendations_a")
    product_b = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="recommendations_b")
    generated_at = models.DateTimeField(auto_now_add=True)
    verified_at = models.DateTimeField(default=timezone.now)
    is_current = models.BooleanField(default=True)
    metrics = models.JSONField(default=dict)  # Internal evidence, never ordinary UI payloads.
    sent_at = models.DateTimeField(null=True, blank=True)
    sent_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True,
        on_delete=models.SET_NULL, related_name="highlighted_bundle_recommendations")

    class Meta:
        db_table = "campushub_bundle_recommendation"
        ordering = ("-generated_at", "-pk")
        constraints = [
            models.UniqueConstraint(fields=("product_a", "product_b"), name="recommendation_pair_unique"),
            models.CheckConstraint(condition=models.Q(product_a__lt=models.F("product_b")),
                                   name="recommendation_pair_ordered"),
        ]


class SellerBundleSuggestion(models.Model):
    """A mobile seller's saved/dismissed live pair; never inventory or a bundle."""
    seller = models.ForeignKey(CampusHubUser, db_constraint=False, on_delete=models.CASCADE,
                               related_name="bundle_suggestion_choices")
    product_a = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="saved_pair_a")
    product_b = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="saved_pair_b")
    state = models.CharField(max_length=10, choices=(("saved", "Saved"), ("dismissed", "Dismissed")))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "campushub_seller_bundle_suggestion"
        ordering = ("-updated_at", "-pk")
        constraints = [
            models.UniqueConstraint(fields=["seller", "product_a", "product_b"], name="seller_bundle_pair_unique"),
            models.CheckConstraint(condition=models.Q(product_a__lt=models.F("product_b")), name="seller_bundle_pair_ordered"),
        ]


class PushDeviceRegistration(models.Model):
    """One FCM installation, bound to an authenticated mobile login session."""
    user = models.ForeignKey(CampusHubUser, db_constraint=False, on_delete=models.CASCADE,
                             related_name="push_devices")
    installation_id = models.CharField(max_length=160, unique=True)
    session_digest = models.CharField(max_length=64)
    valid_until = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "campushub_push_device"


class ProductApprovalPush(models.Model):
    """Review delivery outbox; approved_at retains its legacy review-time name."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="approval_pushes")
    device = models.ForeignKey(PushDeviceRegistration, on_delete=models.CASCADE,
                               related_name="approval_pushes")
    recipient = models.ForeignKey(CampusHubUser, db_constraint=False, on_delete=models.CASCADE,
                                  related_name="product_approval_pushes")
    approved_at = models.DateTimeField()
    decision = models.CharField(max_length=10, default="approved",
                               choices=(("approved", "Approved"), ("rejected", "Rejected")))
    session_digest = models.CharField(max_length=64)
    status = models.CharField(max_length=12, default="pending", choices=(
        ("pending", "Pending"), ("sent", "Sent"), ("failed", "Failed"), ("skipped", "Skipped")))
    attempts = models.PositiveSmallIntegerField(default=0)
    error_code = models.CharField(max_length=80, blank=True)
    retry_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "campushub_product_approval_push"
        constraints = [models.UniqueConstraint(fields=["product", "device", "approved_at", "decision"],
                                               name="product_review_device_once")]
        indexes = [models.Index(fields=["status", "retry_at"], name="approval_push_retry")]
