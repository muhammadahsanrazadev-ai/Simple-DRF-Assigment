"""URL configuration for the project."""

from django.contrib import admin
from django.urls import include, path, re_path
from rest_framework import permissions
from rest_framework_simplejwt.views import TokenRefreshView
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from app.views.user_view import CustomTokenObtainPairView

# Swagger / ReDoc schema configuration
schema_view = get_schema_view(
    openapi.Info(
        title="User Management API",
        default_version="v1",
        description="API for User CRUD with JWT Authentication",
        contact=openapi.Contact(email="admin@example.com"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path("admin/", admin.site.urls),

    # JWT Authentication
    path("api/auth/login/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),

    # App routes
    path("api/", include("app.urls")),

    # Swagger UI
    re_path(r"^swagger/$", schema_view.with_ui("swagger", cache_timeout=0), name="schema-swagger-ui"),
    re_path(r"^redoc/$", schema_view.with_ui("redoc", cache_timeout=0), name="schema-redoc"),
]