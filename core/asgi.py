import os
from django.core.asgi import get_asgi_application

# Set the settings module for the ASGI server
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

application = get_asgi_application()
