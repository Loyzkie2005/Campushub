from django.apps import AppConfig


class NotificationsModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.notifications'
    label = 'campushub_notifications_module'
