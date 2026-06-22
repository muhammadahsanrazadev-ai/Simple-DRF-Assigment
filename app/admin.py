"""
Registers the custom User model with Django admin.

This is purely a convenience for local development/testing (so you can
create/deactivate users visually at /admin/ without calling the API) — the
actual application uses the DRF endpoints in views.py.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("username", "email", "is_superuser", "is_active", "date_joined")
    list_filter = ("is_superuser", "is_active")
