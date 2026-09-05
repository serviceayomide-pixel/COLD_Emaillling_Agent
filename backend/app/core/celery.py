from celery import Celery
from app.core.config import settings

celery_app = Celery(
    "outreach_worker",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=["app.tasks.email_tasks", "app.tasks.outreach_tasks"]
)

print("DEBUG CELERY BROKER_URL CONFIG:", celery_app.conf.broker_url)
print("DEBUG CELERY BACKEND_URL CONFIG:", celery_app.conf.result_backend)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600, # 1 hour max
    worker_prefetch_multiplier=1, # Ensures workers only take 1 task at a time for better distribution
)

# Configure celery beat schedule for recurring background tasks
celery_app.conf.beat_schedule = {
    "run_outreach_pipeline_every_minute": {
        "task": "app.tasks.outreach_tasks.run_outreach_pipeline",
        "schedule": 60.0, # Every 60 seconds
    },
    "renew_microsoft_graph_webhooks": {
        "task": "app.tasks.email_tasks.renew_webhooks",
        "schedule": 43200.0, # Every 12 hours (safety margin for 2.5-day expiration)
    }
}
