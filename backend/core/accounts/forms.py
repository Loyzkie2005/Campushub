from django import forms
from django.contrib.auth.forms import UserChangeForm
from django.contrib.auth.forms import UserCreationForm

from .models import Role, User


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

    class Meta:
        model = User
        fields = (
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
