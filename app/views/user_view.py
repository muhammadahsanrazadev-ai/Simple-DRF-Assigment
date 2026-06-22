"""Views for User CRUD and custom JWT login.

UserViewSet               -> Full CRUD for the User model (JWT required).
CustomTokenObtainPairView -> Login endpoint with input-level validation.
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from core.celery_utils import safe_enqueue
from app.models.customer import User
from app.serializers.user_serializer import (
    UserCreateSerializer,
    UserSerializer,
    CustomTokenObtainPairSerializer,
)
from app.tasks import send_welcome_email


class UserViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for the User model.

    GET    /api/users/        -> List all users
    POST   /api/users/        -> Create user (sends welcome email in background)
    GET    /api/users/{id}/   -> Retrieve a user
    PATCH  /api/users/{id}/   -> Update a user
    DELETE /api/users/{id}/   -> Delete a user
    """

    queryset = User.objects.all().order_by("-date_joined")
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        # Use the create serializer (with password) only on POST
        if self.action == "create":
            return UserCreateSerializer
        return UserSerializer

    def perform_create(self, serializer):
        user = serializer.save()
        # Fire welcome email via Celery (non-blocking, runs in background)
        safe_enqueue(send_welcome_email, user.id)


class CustomTokenObtainPairView(TokenObtainPairView):
    """Login view using the custom serializer that validates input format first."""
    serializer_class = CustomTokenObtainPairSerializer
