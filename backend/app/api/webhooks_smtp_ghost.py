from fastapi import APIRouter, Request, HTTPException
from supabase import create_client, Client
from app.core.config import settings
from datetime import datetime

router = APIRouter()

@router.post("/webhooks/smtp-ghost")
async def smtp_ghost_webhook(request: Request):
    """
    Listens for events from SMTP Ghost (e.g. 'sent', 'opened', 'clicked', 'replied', 'bounced').
    Saves them directly to the Supabase `campaign_logs` table for Real-Time Dashboard tracking.
    """
    # Use SERVICE ROLE KEY to bypass RLS
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    event_type = payload.get("event") or payload.get("type")
    email_address = payload.get("email") or payload.get("recipient")
    
    if not email_address or not event_type:
        return {"status": "ignored", "reason": "missing email or event type"}
    
    # 1. Lookup the CQC Location ID from the `cqc_leads` table using the email
    lead_resp = supabase.table("cqc_leads").select("cqc_location_id").eq("contact_email", email_address).execute()
    
    cqc_location_id = None
    if lead_resp.data and len(lead_resp.data) > 0:
        cqc_location_id = lead_resp.data[0]["cqc_location_id"]
        
    # 2. Insert the event into `campaign_logs` — only columns that exist in the table
    log_data = {
        "event_type": event_type,
    }
    
    if cqc_location_id:
        log_data["cqc_location_id"] = cqc_location_id
        
        # Update the overall status in cqc_leads if it's a critical event
        if event_type in ["bounced", "complained"]:
            supabase.table("cqc_leads").update({"enrichment_status": "bounced"}).eq("cqc_location_id", cqc_location_id).execute()
            
    supabase.table("campaign_logs").insert(log_data).execute()
    
    return {"status": "success", "event": event_type, "email": email_address}
