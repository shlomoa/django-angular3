from django.contrib import admin
from django.urls import include, path
from rest_framework import routers
from shop import views

from django_angular3.spa import angular_urlpatterns

router = routers.DefaultRouter()
router.register(r"customers", views.CustomerViewSet, basename="customer")
router.register(r"products", views.ProductViewSet, basename="product")

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include(router.urls)),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    # Last: Django's own routes win, every other path is the Angular application.
    *angular_urlpatterns(),
]
