from celery import shared_task
import asyncio
from app.worker import run_pipeline

@shared_task(name="app.tasks.outreach_tasks.run_outreach_pipeline")
def run_outreach_pipeline():
    """
    Celery task that runs the outreach worker pipeline.
    This wraps the existing async run_pipeline() function from app.worker.
    """
    asyncio.run(run_pipeline())
