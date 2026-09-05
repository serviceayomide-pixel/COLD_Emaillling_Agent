import os
import sys

# We will use the Celery app instance to purge the queue.
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from backend.app.core.celery import celery_app

print("Purging Celery Queue...")
purged_count = celery_app.control.purge()
print(f"Purged {purged_count} tasks from the queue!")
