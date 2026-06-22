"""
Celery app setup for the project.

Run worker:  celery -A core worker -l info --pool=solo
Run beat:    celery -A core beat -l info
"""

import os
from celery import Celery

# Tell Celery which Django settings to use
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

app = Celery("core")

# Load CELERY_* settings from Django's settings.py
app.config_from_object("django.conf:settings", namespace="CELERY")

# Explicitly tell Celery where to look for tasks
# This is important when the app folder structure is non-standard
app.autodiscover_tasks(["app"])
