"""URL routing for the app module."""

from django.urls import path
from app.views.user_view import UserListCreateAPIView, UserDetailAPIView

urlpatterns = [
    path("users/", UserListCreateAPIView.as_view(), name="user-list-create"),
    path("users/<int:pk>/", UserDetailAPIView.as_view(), name="user-detail"),
]
