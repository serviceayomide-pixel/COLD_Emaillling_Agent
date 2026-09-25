from fastapi import APIRouter
from fastapi.responses import Response
from datetime import datetime, timezone, timedelta

router = APIRouter()

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
            from app.models.models import CqcLead, CampaignLog
            lead = db.query(CqcLead).filter(CqcLead.id == lead_id).first()

            if lead:
                # ANTI-FALSE-OPEN: When the sender views their own sent items,
                # Outlook loads the pixel too. Ignore opens within 2 minutes of sending.
                if lead.emailed_at:
                    emailed_at = lead.emailed_at
                    if emailed_at.tzinfo is None:
                        emailed_at = emailed_at.replace(tzinfo=timezone.utc)
                    seconds_since_sent = (datetime.now(timezone.utc) - emailed_at).total_seconds()
                    if seconds_since_sent < 120:
                        print(f"Lead {lead_id} open ignored (only {int(seconds_since_sent)}s after send — likely sender viewing sent items)")
                        # Still return the pixel but don't log
                        return Response(
                            content=TRANSPARENT_PIXEL,
                            media_type="image/gif",
                            headers={
                                "Cache-Control": "no-store, no-cache, must-revalidate, max-age=0",
                                "Pragma": "no-cache",
                                "Expires": "0"
                            }
                        )

                # Check if an email_opened event already exists for THIS specific lead
                existing = db.query(CampaignLog).filter(
                    CampaignLog.lead_id == lead.id,
                    CampaignLog.event_type == 'email_opened'
                ).first()
                    
                if not existing:
                    new_log = CampaignLog(
                        lead_id=lead.id,
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
