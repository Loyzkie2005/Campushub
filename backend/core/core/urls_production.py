"""Production-only media adapter plus all existing CampusHub routes."""

from django.urls import path

from .media_views import catalog_image
from .urls import urlpatterns as application_urls


urlpatterns = [
    path('media/<path:image_path>', catalog_image, name='catalog_image'),
    *application_urls,
]
