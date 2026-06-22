"""Serializers for User model.

UserSerializer                  -> Read-only user representation.
UserCreateSerializer            -> Create user with strong validation.
UserUpdateSerializer            -> Update user details.
CustomTokenObtainPairSerializer -> JWT login with input-level validation.
"""

import re

from django.contrib.auth.password_validation import validate_password
from django.core.validators import validate_email as django_validate_email
from django.core.exceptions import ValidationError as DjangoValidationError
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from app.models.customer import User


class UserSerializer(serializers.ModelSerializer):
    """Read-only user representation returned in list and retrieve responses."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "is_active", "is_superuser", "date_joined"]
        read_only_fields = fields


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating user details."""

    class Meta:
        model = User
        fields = ["first_name", "last_name", "email"]

    def validate_email(self, value):
        """Email: must be valid format and not already registered to another user."""
        try:
            django_validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Enter a valid email address.")
        
        user = self.instance
        if user and User.objects.exclude(pk=user.pk).filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value



class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new user with strong input validation."""

    # write_only ensures password never appears in API responses
    password = serializers.CharField(
        write_only=True,
        validators=[validate_password],
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "password"]

    def validate_username(self, value):
        """Username: 3-30 chars, alphanumeric + underscores only, must be unique."""
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", value):
            raise serializers.ValidationError(
                "Username must be 3–30 characters: letters, numbers, or underscores only."
            )
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("This username is already taken.")
        return value

    def validate_email(self, value):
        """Email: must be valid format and not already registered."""
        try:
            django_validate_email(value)
        except DjangoValidationError:
            raise serializers.ValidationError("Enter a valid email address.")
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("This email is already in use.")
        return value

    def validate_password(self, value):
        """Password: min 8 chars, must include uppercase, lowercase, digit, and special char."""
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        if not re.search(r"[A-Z]", value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        if not re.search(r"[a-z]", value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        if not re.search(r"[0-9]", value):
            raise serializers.ValidationError("Password must contain at least one number.")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        return value

    def create(self, validated_data):
        """Hash the password and create the user."""
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Extends the default JWT login serializer.
    Validates input format before hitting the database.
    """

    def validate(self, attrs):
        username = attrs.get("username", "")
        password = attrs.get("password", "")

        # Username format check
        if not re.match(r"^[a-zA-Z0-9_]{3,30}$", username):
            raise serializers.ValidationError(
                {"username": "Username must be 3–30 characters: letters, numbers, or underscores only."}
            )

        # Password strength checks
        if len(password) < 8:
            raise serializers.ValidationError({"password": "Password must be at least 8 characters long."})
        if not re.search(r"[A-Z]", password):
            raise serializers.ValidationError({"password": "Password must contain at least one uppercase letter."})
        if not re.search(r"[a-z]", password):
            raise serializers.ValidationError({"password": "Password must contain at least one lowercase letter."})
        if not re.search(r"[0-9]", password):
            raise serializers.ValidationError({"password": "Password must contain at least one number."})
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
            raise serializers.ValidationError({"password": "Password must contain at least one special character."})

        # Delegate actual credential check to SimpleJWT
        return super().validate(attrs)
