from fastapi import APIRouter, Request, Query, Response
from typing import Optional
from app.tasks.email_tasks import process_incoming_webhook
import json
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.post("/webhooks/graph")
async def graph_webhook(request: Request, validationToken: Optional[str] = Query(None)):
    """
    Microsoft Graph Webhook Receiver Endpoint.
    Handles both validation handshakes and incoming notifications.
    """
    # 1. Validation Handshake
    if validationToken:
        logger.info("Received MS Graph webhook validation request.")
        return Response(content=validationToken, media_type="text/plain", status_code=200)

    # 2. Process Notifications
    try:
        body = await request.json()
        logger.info(f"Received MS Graph webhook notification: {json.dumps(body)}")
        
        # Dispatch to Celery for processing in the background (deduplicated in the task)
        # We don't want to block the webhook response
        if "value" in body:
            for notification in body["value"]:
                process_incoming_webhook.delay(notification)
                
        return Response(status_code=202)
    except Exception as e:
        logger.error(f"Error processing webhook: {e}")
        return Response(status_code=500)
