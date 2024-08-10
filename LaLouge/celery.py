# celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'LaLouge.settings')

# create a Celery instance and configure it using the settings from Django
celery_app = Celery('LaLouge')

# Load task modules from all registered Django app configs.
celery_app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
celery_app.autodiscover_tasks()

# Retry Celery Broker Connection Retries Upon Startup
celery_app.conf.broker_connection_retry_on_startup = True


# # Celery Beat configuration
# celery_app.conf.beat_schedule = {
#     "delete_unverified_accounts": {
#         "task": "utilities.tasks.clean_up_unverified_accounts",
#         "schedule": crontab(minute=1),
#     },
# }