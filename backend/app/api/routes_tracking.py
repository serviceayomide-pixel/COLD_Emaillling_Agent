from fastapi import APIRouter
from fastapi.responses import Response
from supabase import create_client, Client
from app.core.config import settings
from datetime import datetime, timezone

router = APIRouter()

# We will instantiate the client inside the route to prevent import-time crashes
# if the environment variable is missing during build/startup.

# A 1x1 transparent GIF pixel (43 bytes)
TRANSPARENT_PIXEL = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00,
    0x01, 0x00, 0x80, 0x00, 0x00, 0xff, 0xff, 0xff,
    0x00, 0x00, 0x00, 0x21, 0xf9, 0x04, 0x01, 0x00,
    0x00, 0x00, 0x00, 0x2c, 0x00, 0x00, 0x00, 0x00,
    0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3b
])


@router.get("/tracking/open/{lead_id}")
async def track_open(lead_id: str):
    """
    When a prospect opens the email, their email client loads this invisible image.
    We log the 'email_opened' event and return a 1x1 transparent pixel.
    """
    try:
        from app.core.database import SessionLocal
        db = SessionLocal()
        
        try:
            # Look up the lead to get the cqc_location_id
            from app.models.models import CqcLead, CampaignLog
            lead = db.query(CqcLead).filter(CqcLead.id == lead_id).first()

            if lead:
                # Check if an email_opened event already exists for this lead
                existing = db.query(CampaignLog).filter(
                    CampaignLog.cqc_location_id == lead.cqc_location_id,
                    CampaignLog.event_type == 'email_opened'
                ).first()
                    
                if not existing:
                    # Log the open event into campaign_logs
                    new_log = CampaignLog(
                        cqc_location_id=lead.cqc_location_id,
                        event_type="email_opened"
                    )
                    db.add(new_log)
                    db.commit()
                    print(f"Tracked FIRST OPEN for lead {lead_id} ({lead.contact_email})")
                else:
                    print(f"Lead {lead_id} already opened the email previously, skipping duplicate log.")
            else:
                print(f"No lead found for id {lead_id} — pixel served but no log written")
        finally:
            db.close()

    except Exception as e:
        # Never fail the pixel response — silently log the error
        print(f"Error tracking open for lead {lead_id}: {e}")

    # Always return the transparent pixel so the email renders correctly
    return Response(
        content=TRANSPARENT_PIXEL,
        media_type="image/gif",
        headers={
            "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
            "Pragma": "no-cache",
            "Expires": "0"
        }
    )
