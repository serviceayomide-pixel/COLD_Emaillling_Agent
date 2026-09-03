from fastapi import APIRouter, Request, HTTPException
from supabase import create_client, Client
from app.core.config import settings
from datetime import datetime

router = APIRouter()

@router.post("/webhooks/cal")
async def cal_webhook(request: Request):
    """
    Listens for booking events from Cal.com.
    """
    # Use SERVICE ROLE KEY to bypass RLS
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
    triggerEvent = payload.get("triggerEvent")
    
    # We only care about bookings created or cancelled
    if triggerEvent not in ["BOOKING_CREATED", "BOOKING_CANCELLED"]:
        return {"status": "ignored", "reason": "unhandled event type"}
        
    payload_data = payload.get("payload", {})
    attendee = payload_data.get("attendees", [{}])[0]
    attendee_email = attendee.get("email")
    attendee_name = attendee.get("name")
    
    start_time = payload_data.get("startTime")
    end_time = payload_data.get("endTime")
    status = payload_data.get("status")
    meeting_url = payload_data.get("metadata", {}).get("videoCallUrl")
    
    if not attendee_email:
        return {"status": "ignored", "reason": "no attendee email"}
        
    # Lookup the lead by email
    lead_resp = supabase.table("cqc_leads").select("cqc_location_id").eq("contact_email", attendee_email).execute()
    cqc_location_id = None
    if lead_resp.data and len(lead_resp.data) > 0:
        cqc_location_id = lead_resp.data[0]["cqc_location_id"]
        
    if triggerEvent == "BOOKING_CREATED":
        # Insert into meetings
        meeting_data = {
            "cqc_location_id": cqc_location_id,
            "attendee_name": attendee_name,
            "attendee_email": attendee_email,
            "start_time": start_time,
            "end_time": end_time,
            "status": status,
            "meeting_url": meeting_url
        }
        supabase.table("meetings").insert(meeting_data).execute()
        
        # Update lead status
        if cqc_location_id:
            supabase.table("cqc_leads").update({"campaign_status": "booked"}).eq("cqc_location_id", cqc_location_id).execute()
            
            # Log the event
            supabase.table("campaign_logs").insert({
                "cqc_location_id": cqc_location_id,
                "event_type": "meeting_booked"
            }).execute()
            
    elif triggerEvent == "BOOKING_CANCELLED":
        # We can update the meeting status if we had a unique meeting UID, 
        # but for simplicity we'll just update based on email and start time.
        if start_time:
            supabase.table("meetings").update({"status": "CANCELLED"}).eq("attendee_email", attendee_email).eq("start_time", start_time).execute()
            
        if cqc_location_id:
            supabase.table("cqc_leads").update({"campaign_status": "interested"}).eq("cqc_location_id", cqc_location_id).execute()
            
            supabase.table("campaign_logs").insert({
                "cqc_location_id": cqc_location_id,
                "event_type": "meeting_cancelled"
            }).execute()

    return {"status": "success"}
