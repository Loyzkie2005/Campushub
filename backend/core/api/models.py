from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.db import models
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
    is_active = models.BooleanField(default=True)
    is_suspended = models.BooleanField(default=False)
    profile_completed = models.BooleanField(default=False)
    last_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        managed = False
        db_table = "campushub_user"

    def __str__(self):
        return self.username


class Product(models.Model):
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
    )
    product_code = models.CharField(max_length=13, unique=True, blank=True, null=True)
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=80, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.PositiveIntegerField(default=0)
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

    class Meta:
        db_table = "campushub_product"
        ordering = ("-submitted_at",)
        permissions = (
            ("can_view_seller_products", "Can view seller products"),
            ("can_approve_seller_products", "Can approve seller products"),
        )

    def __str__(self):
        return self.name

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
        self.approval_status = self.STATUS_APPROVED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.rejection_reason = ""
        self.save(update_fields=[
            "approval_status",
            "approved_by",
            "approved_at",
            "rejection_reason",
            "updated_at",
        ])

    def reject(self, user, reason=""):
        self.approval_status = self.STATUS_REJECTED
        self.approved_by = user
        self.approved_at = timezone.now()
        self.rejection_reason = reason
        self.save(update_fields=[
            "approval_status",
            "approved_by",
            "approved_at",
            "rejection_reason",
            "updated_at",
        ])

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

    STATUS_CHOICES = (
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
    )

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "campushub_seller_request"
        ordering = ("-created_at",)
        permissions = (
            ("can_view_seller_requests", "Can view seller requests"),
            ("can_approve_seller_requests", "Can approve seller requests"),
        )

    def __str__(self):
        return f"{self.full_name} - {self.product_type}"

    def approve(self, user):
        self.status = self.STATUS_APPROVED
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.rejection_reason = ""
        if self.user_id:
            self.user.role = "Seller"
            self.user.save(update_fields=["role"])
        self.save(update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "updated_at",
        ])

    def reject(self, user, reason=""):
        self.status = self.STATUS_REJECTED
        self.reviewed_by = user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save(update_fields=[
            "status",
            "reviewed_by",
            "reviewed_at",
            "rejection_reason",
            "updated_at",
        ])


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
        (TYPE_HOSTEL, "Hostel Accommodation"),
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
    """Mobile request details kept alongside the existing booking record."""

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
