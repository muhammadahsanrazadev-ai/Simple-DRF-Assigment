"""Views for User CRUD and custom JWT login.

UserViewSet               -> Full CRUD for User model (JWT required)
CustomTokenObtainPairView -> Login endpoint with validation
"""

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView

from core.celery_utils import safe_enqueue
from app.models.customer import User
from app.serializers.user_serializer import (
    UserCreateSerializer,
    UserSerializer,
    UserUpdateSerializer,
    CustomTokenObtainPairSerializer,
)
from app.tasks import send_welcome_email, send_email_update_notification


from django.http import Http404
from rest_framework import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework.exceptions import PermissionDenied


class UserListCreateAPIView(generics.GenericAPIView):
    """
    User GET (List) and POST (Create) API.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request and self.request.method == "POST":
            return UserCreateSerializer
        return UserSerializer

    def get(self, request):
        """
        List users. Superuser sees all, normal user sees only themselves.
        """
        user = request.user
        if user.is_superuser:
            users = User.objects.all().order_by("-date_joined")
        else:
            users = User.objects.filter(id=user.id)
            
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        """
        Create a new user. Only superusers can perform this action.
        """
        if not request.user.is_superuser:
            raise PermissionDenied("Only superusers can create new users.")

        serializer = UserCreateSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Async welcome email (Celery)
            safe_enqueue(send_welcome_email, user.id)
            
            # Return read-only data
            return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailAPIView(generics.GenericAPIView):
    """
    User GET (Retrieve), PUT/PATCH (Update), and DELETE API.
    """
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.request and self.request.method in ["PUT", "PATCH"]:
            return UserUpdateSerializer
        return UserSerializer

    def get_object(self, pk, user):
        """
        Helper method to get the user object.
        Ensures normal users can only access their own record.
        """
        try:
            if user.is_superuser:
                return User.objects.get(pk=pk)
            # Normal users can only fetch themselves
            return User.objects.get(pk=pk, id=user.id)
        except User.DoesNotExist:
            raise Http404

    def get(self, request, pk):
        """
        Retrieve a specific user.
        """
        user_obj = self.get_object(pk, request.user)
        serializer = UserSerializer(user_obj)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def put(self, request, pk):
        """
        Update user fully.
        """
        return self._update(request, pk, partial=False)

    def patch(self, request, pk):
        """
        Update user partially.
        """
        return self._update(request, pk, partial=True)

    def _update(self, request, pk, partial):
        user_obj = self.get_object(pk, request.user)
        old_email = user_obj.email
        
        # Use update serializer
        serializer = UserUpdateSerializer(user_obj, data=request.data, partial=partial)
        if serializer.is_valid():
            # Extra safety: ensure normal user cannot escalate privileges if someone injected fields
            if not request.user.is_superuser:
                serializer.validated_data.pop("is_superuser", None)
                serializer.validated_data.pop("is_staff", None)
                
            new_email = serializer.validated_data.get("email", old_email)
            email_changed = (old_email != new_email)
            
            updated_user = serializer.save()
            
            # Feature: Notify user if superuser changes their email
            if email_changed and request.user.is_superuser and request.user.id != updated_user.id:
                safe_enqueue(send_email_update_notification, updated_user.username, old_email, new_email)
                
            # Return read-only serializer output after save
            return Response(UserSerializer(updated_user).data, status=status.HTTP_200_OK)
            
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        """
        Delete a user.
        """
        user_obj = self.get_object(pk, request.user)
        user_obj.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    JWT login endpoint with custom validation serializer
    """
    serializer_class = CustomTokenObtainPairSerializer