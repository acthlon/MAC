import os

from celery import Celery

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MAC.settings")
app = Celery("MAC")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
