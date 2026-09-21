"""Persistent records for reports generated from the admin portal."""

from django.conf import settings
from django.db import models


class GeneratedReport(models.Model):
    REPORT_TYPES = (
        ("sales", "Sales Report"),
        ("orders", "Orders Report"),
        ("products", "Product & Inventory Report"),
        ("low_stock", "Low Stock Report"),
        ("bookings", "Facility Booking Report"),
        ("facility_utilization", "Facility Utilization Report"),
        ("facility_payments", "Facility Payments & OR Report"),
        ("user_accounts", "User Accounts Report"),
        ("user_activity", "User Login Activity Report"),
    )
    FILE_FORMATS = (
        ("csv", "CSV"),
        ("pdf", "PDF"),
    )

    generated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name="generated_reports",
    )
    report_type = models.CharField(max_length=24, choices=REPORT_TYPES)
    file_format = models.CharField(max_length=8, choices=FILE_FORMATS)
    date_from = models.DateField(null=True, blank=True)
    date_to = models.DateField(null=True, blank=True)
    row_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "campushub_generated_report"
        ordering = ("-created_at",)

    def __str__(self):
        return f"{self.get_report_type_display()} ({self.file_format.upper()})"
