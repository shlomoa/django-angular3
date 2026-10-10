"""URL configuration of ``tests/test_spa.py``: a Django route ahead of Angular."""

from django.http import JsonResponse
from django.urls import path

from django_angular3.spa import angular_urlpatterns


def ping(request):
    return JsonResponse({"ok": True})


urlpatterns = [
    path("api/v1/ping/", ping),
    *angular_urlpatterns(),
]
