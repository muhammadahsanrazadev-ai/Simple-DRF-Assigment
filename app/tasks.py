"""Celery background tasks for the app module."""

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail


@shared_task
def send_welcome_email(user_id):
    """
    Sends a welcome email to a newly created user.
    Receives user_id (not the object) because Celery serializes args to JSON.
    """
    from app.models.customer import User  # Local import to avoid app-loading issues

    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return  # User deleted before task ran — nothing to do

    send_mail(
        subject="Welcome to Our Platform",
        message=(
            f"Hi {user.username},\n\n"
            "Your account has been successfully created. "
            "You can now log in and start using our services.\n\n"
            "— The Team"
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
