from celery import shared_task
import asyncio
from scripts.manage_graph_webhooks import manage_webhooks

@shared_task(name="app.tasks.email_tasks.renew_webhooks")
def renew_webhooks():
    """
    Periodic task to renew MS Graph Webhooks before they expire (every 2.9 days max).
    We run this daily.
    """
    asyncio.run(manage_webhooks())

@shared_task(name="app.tasks.email_tasks.process_incoming_webhook")
def process_incoming_webhook(webhook_payload: dict):
    """
    Task to process an incoming Microsoft Graph webhook asynchronously.
    """
    asyncio.run(process_webhook_async(webhook_payload))

async def process_webhook_async(payload: dict):
    from app.core.config import settings
    from app.services.imap_reader import get_graph_token
    from app.core.database import SessionLocal
    from app.models.models import CqcLead, CampaignLog, OutlookMessage
    from app.services.openrouter import analyze_reply_intent
    import httpx
    from datetime import datetime, timezone, timedelta

    print(f"Processing webhook notification...")
    resource_data = payload.get("resourceData", {})
    message_id = resource_data.get("id")
    
    if not message_id:
        print("No message ID found in webhook payload.")
        return

    db = SessionLocal()
    try:
        # Check if we already processed this message ID to avoid duplicate work
        existing_msg = db.query(OutlookMessage).filter(OutlookMessage.message_id == message_id).first()
        if existing_msg:
            print(f"Message {message_id} already processed. Skipping.")
            return

        token = await get_graph_token()
        if not token:
            print("Failed to get Graph token for webhook processing.")
            return

        email_address = settings.MICROSOFT_EMAIL
        if not email_address:
            print("MICROSOFT_EMAIL not configured.")
            return
            
        email_address_lower = email_address.lower()

        # Fetch the full message from Graph API
        url = f"https://graph.microsoft.com/v1.0/users/{email_address}/messages/{message_id}"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers, timeout=15.0)
            if response.status_code != 200:
                print(f"Failed to fetch message {message_id} from Graph: {response.text}")
                return
            msg = response.json()

        conversation_id = msg.get("conversationId")
        sender = msg.get("from", {}).get("emailAddress", {}).get("address", "").lower()
        subject = msg.get("subject", "")
        
        # Determine if it's Sent or Inbox
        is_sent_item = (sender == email_address_lower)
        
        # Extract body
        body = msg.get("bodyPreview", "")
        if msg.get("body", {}).get("contentType") == "text":
            body = msg.get("body", {}).get("content", body)
        elif msg.get("body", {}).get("contentType") == "html":
            body = msg.get("bodyPreview", body)

        # Helper to parse receivedDateTime
        date_str = msg.get("receivedDateTime")
        if not date_str:
            msg_received_at = datetime.now(timezone.utc)
        else:
            try:
                msg_received_at = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except Exception:
                msg_received_at = datetime.now(timezone.utc)

        now_utc = datetime.now(timezone.utc)

        if is_sent_item:
            # PROCESS AS SENT ITEM
            to_recipients = msg.get("toRecipients", [])
            if not to_recipients:
                return
            recipient = to_recipients[0].get("emailAddress", {}).get("address", "").lower()
            
            lead = db.query(CqcLead).filter(CqcLead.contact_email == recipient).first()
            if not lead:
                return
                
            print(f"[Webhook] New Sent Message to lead: {recipient} - {subject}")
            new_msg = OutlookMessage(
                message_id=message_id,
                conversation_id=conversation_id,
                lead_id=lead.id,
                folder="sentitems",
                sender_email=email_address_lower,
                recipient_email=recipient,
                subject=subject,
                body=body.strip(),
                received_at=msg_received_at
            )
            db.add(new_msg)
            
            if lead.campaign_status == 'not_started' and msg_received_at >= now_utc - timedelta(minutes=5):
                lead.campaign_status = 'active'
                lead.emailed_at = msg_received_at
            db.commit()

        else:
            # PROCESS AS INBOX REPLY
            lead = None
            if conversation_id:
                outbox_msg = db.query(OutlookMessage).filter(OutlookMessage.conversation_id == conversation_id, OutlookMessage.folder == 'sentitems').first()
                if outbox_msg:
                    lead = db.query(CqcLead).filter(CqcLead.id == outbox_msg.lead_id).first()
            
            if not lead:
                lead = db.query(CqcLead).filter(CqcLead.contact_email == sender).first()
                
            if not lead:
                return # Not a lead

            if not lead.emailed_at or msg_received_at < lead.emailed_at:
                return # Safety check

            print(f"[Webhook] New Inbox Message from lead: {lead.company_name} (Sender: {sender})")
            new_msg = OutlookMessage(
                message_id=message_id,
                conversation_id=conversation_id,
                lead_id=lead.id,
                folder="inbox",
                sender_email=sender,
                recipient_email=email_address_lower,
                subject=subject,
                body=body.strip(),
                received_at=msg_received_at
            )
            db.add(new_msg)
            db.commit()

            # Process reply classification
            previous_status = lead.campaign_status
            intent = await analyze_reply_intent(body)
            intent_lower = intent.lower()
            print(f"[Webhook] AI classified reply intent for {lead.company_name} as: {intent}")
            
            log = CampaignLog(
                cqc_location_id=lead.cqc_location_id,
                event_type=f"reply_received: {intent_lower}"
            )
            db.add(log)
            
            if intent_lower in ["not interested", "wrong contact"]:
                print(f"Negative reply from {lead.contact_email}. Keeping lead in database and setting status to {intent_lower}.")
                lead.campaign_status = intent_lower
                db.commit()
            elif intent_lower == "out of office":
                print(f"Out of office reply from {lead.contact_email}. Rescheduling campaign in 7 days.")
                lead.campaign_status = "out of office"
                lead.next_email_date = datetime.now(timezone.utc) + timedelta(days=7)
                db.commit()
            else:
                lead.campaign_status = intent_lower
                db.commit()

                if intent_lower == "interested" and previous_status not in ["interested", "booked"]:
                    from app.services.auto_reply import send_cal_link
                    await send_cal_link(sender, message_id)

    except Exception as e:
        db.rollback()
        print(f"Error processing webhook payload: {e}")
    finally:
        db.close()
    # asyncio.run(process_webhook_async(webhook_payload))
