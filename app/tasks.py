"""Celery background tasks for the app module."""

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)


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

@shared_task
def send_email_update_notification(username, old_email, new_email):
    """
    Sends an email notification to the old email address informing the user
    that their email address has been updated by an admin.
    """
    logger.info(f"Starting send_email_update_notification for {username} - Old Email: {old_email}, New Email: {new_email}")
    try:
        sent = send_mail(
            subject="Security Alert: Your Email Has Been Updated",
            message=(
                f"Hi {username},\n\n"
                "This is a security notification. An administrator has updated the email address "
                f"associated with your account.\n\n"
                f"Old Email: {old_email}\n"
                f"New Email: {new_email}\n\n"
                "If this was a mistake or you did not authorize this change, please contact support immediately.\n\n"
                "— The Team"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[old_email],
            fail_silently=False,
        )
        logger.info(f"Email sent successfully. Result: {sent}")
    except Exception as e:
        logger.error(f"Error sending email: {e}")
        raise
