from django.apps import AppConfig


class UserManagementModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.user_management'
    label = 'campushub_accounts_module'
    verbose_name = 'User Management'
