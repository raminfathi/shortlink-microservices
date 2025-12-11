import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('auth_service')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related config keys should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f'Request: {self.request!r}')

# --- Periodic Tasks Schedule (Celery Beat) ---
app.conf.beat_schedule = {
    'send-report-every-minute': {
        'task': 'users.tasks.generate_daily_report',
        # For testing purposes, we run it every minute.
        # In a real scenario, use crontab(hour=7, minute=30) for daily reports.
        'schedule': crontab(minute='*'),
    },
}