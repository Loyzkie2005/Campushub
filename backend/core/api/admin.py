from django.contrib import admin

from .models import GmailConfig, PasswordResetCode, Product, ProductInteraction, SellerRequest


@admin.action(description="Approve selected products")
def approve_products(modeladmin, request, queryset):
    for product in queryset:
        product.approve(request.user)


@admin.action(description="Reject selected products")
def reject_products(modeladmin, request, queryset):
    for product in queryset:
        product.reject(request.user)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "seller",
        "category",
        "price",
        "stock",
        "approval_status",
        "submitted_at",
    )
    list_filter = ("approval_status", "category", "submitted_at")
    search_fields = ("name", "seller__username", "seller__email", "category")
    readonly_fields = ("submitted_at", "updated_at", "approved_at", "approved_by")
    actions = (approve_products, reject_products)


@admin.action(description="Approve selected seller requests")
def approve_seller_requests(modeladmin, request, queryset):
    for seller_request in queryset:
        seller_request.approve(request.user)


@admin.action(description="Reject selected seller requests")
def reject_seller_requests(modeladmin, request, queryset):
    for seller_request in queryset:
        seller_request.reject(request.user)


@admin.register(GmailConfig)
class GmailConfigAdmin(admin.ModelAdmin):
    list_display = ("gmail_user", "smtp_host", "smtp_port", "is_active", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("gmail_user",)


@admin.register(PasswordResetCode)
class PasswordResetCodeAdmin(admin.ModelAdmin):
    list_display = ("email", "expires_at", "used", "created_at")
    list_filter = ("used",)
    search_fields = ("email",)
    readonly_fields = ("code_hash", "created_at")


@admin.register(ProductInteraction)
class ProductInteractionAdmin(admin.ModelAdmin):
    list_display = ("user_id", "product", "interaction_type", "created_at")
    list_filter = ("interaction_type",)


@admin.register(SellerRequest)
class SellerRequestAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "student_id",
        "product_type",
        "status",
        "created_at",
        "reviewed_by",
    )
    list_filter = ("status", "product_type", "created_at")
    search_fields = ("full_name", "student_id", "course_section", "product_type")
    readonly_fields = ("created_at", "updated_at", "reviewed_at", "reviewed_by")
    actions = (approve_seller_requests, reject_seller_requests)

