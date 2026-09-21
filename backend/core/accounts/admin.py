from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .forms import AdminUserChangeForm, AdminUserCreationForm
from .models import Department, Role, User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    add_form = AdminUserCreationForm
    form = AdminUserChangeForm

    list_display = (
        "username",
        "email",
        "first_name",
        "last_name",
        "role",
        "department",
        "is_staff",
    )

    list_filter = (
        "role",
        "department",
        "is_staff",
        "is_superuser",
        "is_active",
    )

    fieldsets = UserAdmin.fieldsets + (
        ("Extra Info", {"fields": ("role", "department")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "username",
                    "first_name",
                    "last_name",
                    "email",
                    "role",
                    "department",
                    "is_staff",
                    "is_active",
                    "password1",
                    "password2",
                ),
            },
        ),
    )

    search_fields = ("username", "email", "first_name", "last_name")
    ordering = ("email",)


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("role_name", "description", "created_at")
    search_fields = ("role_name", "description")
    ordering = ("role_name",)
