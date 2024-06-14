from __future__ import absolute_import, unicode_literals

import os
from app.pms.celery import Celery
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pms.settings')

app = Celery("app")

app.config_from_object("django.conf:settings:", namespace="CELERY")
app.autodiscover_tasks()
