import os

from celery import Celery


# Konfiguruje Celery do współpracy z Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "myproject.settings")

app = Celery("mojprojekt")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()