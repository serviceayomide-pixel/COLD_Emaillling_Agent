import httpx
from datetime import datetime, timezone, timedelta
from app.core.config import settings
from app.services.imap_reader import get_graph_token
from app.core.database import SessionLocal
from app.models.models import CqcLead, CampaignLog, OutlookMessage, SyncToken
from app.services.openrouter import analyze_reply_intent

async def fetch_folder_messages(folder: str, limit: int = 50) -> list:
    """Fetches messages from a specific Outlook folder via MS Graph API using Delta queries."""
    token = await get_graph_token()
    if not token:
        print("Failed to get Graph token.")
        return []
        
    email_address = settings.MICROSOFT_EMAIL
    db = SessionLocal()
    sync_token = db.query(SyncToken).filter(SyncToken.folder == folder).first()
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    messages = []
    
    try:
        if sync_token and sync_token.delta_token:
            url = sync_token.delta_token
            print(f"Using Delta Token for {folder}...")
            
            async with httpx.AsyncClient() as client:
                while url:
                    response = await client.get(url, headers=headers, timeout=15.0)
                    if response.status_code == 200:
                        data = response.json()
                        messages.extend(data.get("value", []))
                        
                        if "@odata.nextLink" in data:
                            url = data["@odata.nextLink"]
                        elif "@odata.deltaLink" in data:
                            sync_token.delta_token = data["@odata.deltaLink"]
                            db.commit()
                            break
                        else:
                            break
                    else:
                        if response.status_code == 410: # Expired delta token
                            print(f"Delta token expired for {folder}. Resetting...")
                            db.delete(sync_token)
                            db.commit()
                            sync_token = None
                        else:
                            print(f"Graph API Error fetching from {folder}: {response.status_code} - {response.text}")
                        break
        
        # Fallback if no token (or expired)
        if not sync_token or not sync_token.delta_token:
            print(f"WARNING: No Delta Token found for {folder}. Doing standard sync and initializing token.")
            # 1. Fetch standard top N messages
            fallback_url = f"https://graph.microsoft.com/v1.0/users/{email_address}/mailFolders/{folder}/messages?$top={limit}&$orderby=receivedDateTime desc"
            async with httpx.AsyncClient() as client:
                response = await client.get(fallback_url, headers=headers, timeout=15.0)
                if response.status_code == 200:
                    messages.extend(response.json().get("value", []))
            
            # 2. Fetch latest delta token for future syncs
            delta_url = f"https://graph.microsoft.com/v1.0/users/{email_address}/mailFolders/{folder}/messages/delta"
            async with httpx.AsyncClient() as client:
                while delta_url:
                    response = await client.get(delta_url, headers=headers, timeout=15.0)
                    if response.status_code != 200:
                        print(f"Graph API Error initializing delta for {folder}: {response.status_code} - {response.text}")
                        break
                    data = response.json()
                    if "@odata.nextLink" in data:
                        delta_url = data["@odata.nextLink"]
                    elif "@odata.deltaLink" in data:
                        if not sync_token:
                            sync_token = SyncToken(folder=folder, delta_token=data["@odata.deltaLink"])
                            db.add(sync_token)
                        else:
                            sync_token.delta_token = data["@odata.deltaLink"]
                        db.commit()
                        print(f"Initialized Delta Token for {folder}.")
                        break
                    else:
                        break
                        
        return messages
    except Exception as e:
        print(f"Exception connecting to Graph API for {folder}: {e}")
        return []
    finally:
        db.close()

async def sync_outlook_emails():
    """Syncs Inbox and Sent Items from Microsoft Outlook and filters for leads in our database."""
    print("Checking Outlook for real-time lead updates...")
    
    # 1. Sync Inbox
    inbox_messages = await fetch_folder_messages("inbox", limit=50)
    # 2. Sync Sent Items (Outbox)
    sent_messages = await fetch_folder_messages("sentitems", limit=50)
    
    db = SessionLocal()
    try:
        email_address = settings.MICROSOFT_EMAIL
        if not email_address:
            print("Missing MICROSOFT_EMAIL in settings.")
            return
            
        email_address_lower = email_address.lower()
        
        # Helper to parse receivedDateTime
        def parse_date(date_str):
            if not date_str:
                return datetime.now(timezone.utc)
            # Standard MS Graph datetime format: "2026-07-08T08:00:00Z"
            try:
                # Replace Z with +00:00 for python isoformat
                return datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            except Exception:
                return datetime.now(timezone.utc)

        # Process Sent Messages (Outbox) FIRST so we have the conversation_id mapping before Inbox
        for msg in sent_messages:
            msg_id = msg.get("id")
            conversation_id = msg.get("conversationId")
            to_recipients = msg.get("toRecipients", [])
            if not to_recipients:
                continue
                
            recipient = to_recipients[0].get("emailAddress", {}).get("address", "").lower()
            subject = msg.get("subject", "")
            
            # Extract body
            body = msg.get("bodyPreview", "")
            if msg.get("body", {}).get("contentType") == "text":
                body = msg.get("body", {}).get("content", body)
            elif msg.get("body", {}).get("contentType") == "html":
                body = msg.get("bodyPreview", body)

            if not recipient or recipient == email_address_lower:
                continue

            msg_received_at = parse_date(msg.get("receivedDateTime"))
            
            # Look up if recipient is a lead in our database
            lead = db.query(CqcLead).filter(CqcLead.contact_email == recipient).first()
            if not lead:
                continue # Skip non-lead messages

            # Check if already saved in outlook_messages
            existing_msg = db.query(OutlookMessage).filter(OutlookMessage.message_id == msg_id).first()
            if not existing_msg:
                now_utc = datetime.now(timezone.utc)
                
                # If lead is not_started, only track manual sent items if they are from the last 5 minutes
                if lead.campaign_status == 'not_started':
                    if msg_received_at < now_utc - timedelta(minutes=5):
                        continue # Ignore old manual sent items for unstarted leads
                    else:
                        lead.campaign_status = 'active'
                        lead.emailed_at = msg_received_at

                print(f"New Sent Message to lead: {recipient} - {subject}")
                
                # Save message
                new_msg = OutlookMessage(
                    message_id=msg_id,
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
                db.commit()

        # Process Inbox Messages
        for msg in inbox_messages:
            msg_id = msg.get("id")
            conversation_id = msg.get("conversationId")
            sender = msg.get("from", {}).get("emailAddress", {}).get("address", "").lower()
            subject = msg.get("subject", "")
            
            # Extract plain text or html body
            body = msg.get("bodyPreview", "")
            if msg.get("body", {}).get("contentType") == "text":
                body = msg.get("body", {}).get("content", body)
            elif msg.get("body", {}).get("contentType") == "html":
                # Fallback to bodyPreview for a clean text representation, or extract html
                body = msg.get("bodyPreview", body)

            if not sender or sender == email_address_lower:
                continue

            msg_received_at = parse_date(msg.get("receivedDateTime"))

            # Look up lead FIRST by conversation_id (handles forwarded emails and alternate addresses)
            lead = None
            if conversation_id:
                outbox_msg = db.query(OutlookMessage).filter(OutlookMessage.conversation_id == conversation_id, OutlookMessage.folder == 'sentitems').first()
                if outbox_msg:
                    lead = db.query(CqcLead).filter(CqcLead.id == outbox_msg.lead_id).first()
            
            # Fallback to sender email if conversation_id matching fails
            if not lead:
                lead = db.query(CqcLead).filter(CqcLead.contact_email == sender).first()
                
            if not lead:
                continue # Skip non-lead messages (promotions, system, etc.)
                
            # SAFETY CHECK: Ignore replies if we haven't officially emailed them yet
            # or if their reply is from BEFORE we actually emailed them
            if not lead.emailed_at or msg_received_at < lead.emailed_at:
                continue

            # Check if already saved in outlook_messages
            existing_msg = db.query(OutlookMessage).filter(OutlookMessage.message_id == msg_id).first()
            if not existing_msg:
                print(f"New Inbox Message mapped to lead: {lead.company_name} (Sender: {sender})")
                
                # Save message
                new_msg = OutlookMessage(
                    message_id=msg_id,
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
                print(f"AI classified reply intent for {lead.company_name} as: {intent}")
                
                # Log event first (campaign_logs survives lead deletion)
                log = CampaignLog(
                    cqc_location_id=lead.cqc_location_id,
                    event_type=f"reply_received: {intent_lower}"
                )
                db.add(log)
                
                if intent_lower in ["not interested", "wrong contact"]:
                    print(f"Negative reply from {lead.contact_email}. Keeping lead in database and setting status to {intent_lower}.")
                    lead.campaign_status = intent_lower
                    db.commit()
                else:
                    lead.campaign_status = intent_lower
                    db.commit()

                    # Trigger auto-response if interested, BUT prevent infinite loop if already interested/booked!
                    if intent_lower == "interested" and previous_status not in ["interested", "booked"]:
                        print(f"Auto-booking response triggered for {lead.company_name}!")
                        from app.services.auto_reply import send_cal_link
                        await send_cal_link(sender, msg_id)

    except Exception as e:
        db.rollback()
        print(f"Error syncing Outlook emails: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(sync_outlook_emails())
