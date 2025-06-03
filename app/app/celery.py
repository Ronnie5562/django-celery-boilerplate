import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "app.settings")

app = Celery("app")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)

# Optional configuration for production
app.conf.update(
    # Task result life time until they will be deleted
    result_expires=3600,  # 1 hour
    # Worker settings
    worker_prefetch_multiplier=4,  # Adjust based on your workload
    worker_max_tasks_per_child=100,  # Prevent memory leaks
    worker_max_memory_per_child=250000,  # 250MB
    # Queue/routing configuration
    task_default_queue="default",
    task_queues={
        "default": {
            "exchange": "default",
            "exchange_type": "direct",
            "routing_key": "default",
        },
        "high_priority": {
            "exchange": "high_priority",
            "exchange_type": "direct",
            "routing_key": "high_priority",
        },
    },
    # Security settings
    worker_proc_alive_timeout=30,  # seconds
    event_queue_ttl=60,  # seconds
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
)


@app.task(bind=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
