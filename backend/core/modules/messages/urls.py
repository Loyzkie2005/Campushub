from django.urls import path

from .views import chat_contacts, chat_token

app_name = 'module_messages'
urlpatterns = [
    path("token/", chat_token, name="token"),
    path("contacts/", chat_contacts, name="contacts"),
]
