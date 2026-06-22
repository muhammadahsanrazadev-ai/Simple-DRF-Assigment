"""Custom User model extending Django's AbstractUser."""

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # Email is required and must be unique (used for sending notifications)
    email = models.EmailField(unique=True)

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]

    def __str__(self):
        return self.username
