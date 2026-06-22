import os
from django.core.wsgi import get_wsgi_application

# Set the settings module for the WSGI server
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

application = get_wsgi_application()
