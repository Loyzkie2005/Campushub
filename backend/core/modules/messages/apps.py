from django.apps import AppConfig


class MessagesModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'modules.messages'
    label = 'campushub_messages_module'
