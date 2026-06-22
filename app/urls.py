"""URL routing for the app module."""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from app.views.user_view import UserViewSet

# Register UserViewSet under /api/users/
router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

urlpatterns = [
    path("", include(router.urls)),
]
