from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.forms import UserCreationForm
from django.db import connection
from django.db.models import Q

from .models import Department, ProgramMajor, Role, User


def get_role_choices():
    roles = list(
        Role.objects.filter(is_active=True).values_list("role_name", "role_name")
    )
    if roles:
        return roles
    return [("User", "User")]


class AdminUserCreationForm(UserCreationForm):
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    role = forms.ChoiceField(choices=[])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["role"].choices = get_role_choices()
        self.fields["department"].queryset = Department.objects.filter(is_program=True)
        self.fields["major"].queryset = ProgramMajor.objects.select_related("program")

    def clean(self):
        data = super().clean()
        program, major = data.get("department"), data.get("major")
        from .academic import resolve_account_academic
        try:
            data["department"], data["major"] = resolve_account_academic(data.get("role"), "admin", program.pk if program else None, major.pk if major else None)
        except ValueError as exc:
            self.add_error("department", str(exc))
        return data

    class Meta:
        model = User
        fields = (
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "department",
            "major",
            "is_staff",
            "is_active",
            "password1",
            "password2",
        )

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("A user with this email already exists.")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        if commit:
            user.save()
            self.save_m2m()
        return user


class AdminUserChangeForm(UserChangeForm):
    role = forms.ChoiceField(choices=[])

    class Meta:
        model = User
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        choices = get_role_choices()
        current_role = getattr(self.instance, "role", None)
        if current_role and current_role not in [value for value, _ in choices]:
            choices = [(current_role, current_role)] + choices
        self.fields["role"].choices = choices

    def clean(self):
        data = super().clean()
        from .academic import resolve_account_academic
        program, major = data.get("department"), data.get("major")
        try:
            data["department"], data["major"] = resolve_account_academic(data.get("role"), "admin", program.pk if program else None, major.pk if major else None, existing=self.instance)
        except ValueError as exc:
            self.add_error("department", str(exc))
        if self.instance.pk:
            # Django admin wraps form saving in a transaction. Lock in the same
            # order as the custom Users endpoint so two demotions cannot race.
            if connection.in_atomic_block:
                list(User.objects.select_for_update().filter(is_active=True, is_suspended=False)
                     .filter(Q(is_superuser=True) | Q(role__iexact="Super Admin"))
                     .order_by("pk").values_list("pk", flat=True))
            original = User.objects.get(pk=self.instance.pk)
            if original.is_active and not original.is_suspended and (original.is_superuser or original.role.casefold() == "super admin"):
                final = not User.objects.filter(is_active=True, is_suspended=False).exclude(pk=original.pk).filter(Q(is_superuser=True) | Q(role__iexact="Super Admin")).exists()
                if final and (not data.get("is_active") or data.get("is_suspended") or data.get("role", "").casefold() != "super admin"):
                    raise forms.ValidationError("The final active Super Admin cannot be deactivated or demoted.")
        return data
