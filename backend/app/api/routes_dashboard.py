from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.core.database import get_db
from app.models.models import CqcLead, CampaignLog, CampaignMonth, OutlookMessage

router = APIRouter()

@router.get("/dashboard/stats")
def get_dashboard_stats(db: Session = Depends(get_db)):
    """
    Returns high-level statistics for the React Dashboard,
    optionally scoped to the active campaign month.
    """
    # Get active month
    active_month = db.query(CampaignMonth).filter(CampaignMonth.status == 'active').first()
    active_month_number = active_month.month_number if active_month else 1

    # Total Prospects in Database (global for context)
    total_leads = db.query(func.count(CqcLead.id)).scalar() or 0
    
    # Enriched (verified email found)
    enriched_leads = db.query(func.count(CqcLead.id))\
                       .filter(CqcLead.enrichment_status == 'enriched').scalar() or 0
    
    # Emails Sent (emailed_at is not null)
    emails_sent = db.query(func.count(CqcLead.id))\
                    .filter(CqcLead.campaign_month == active_month_number, CqcLead.emailed_at.isnot(None)).scalar() or 0
                    
    # Opened emails for the active month's leads
    opened_count = db.query(func.count(CampaignLog.id))\
                     .join(CqcLead, CampaignLog.cqc_location_id == CqcLead.cqc_location_id)\
                     .filter(CqcLead.campaign_month == active_month_number, CampaignLog.event_type == 'email_opened')\
                     .scalar() or 0

    # Replied Leads for the active month
    replied_count = db.query(func.count(CqcLead.id))\
                      .filter(
                          CqcLead.campaign_month == active_month_number,
                          CqcLead.campaign_status.notin_(['not_started', 'active'])
                      ).scalar() or 0

    # Interested Replies for the active month
    interested = db.query(func.count(CqcLead.id))\
                   .filter(CqcLead.campaign_month == active_month_number, CqcLead.campaign_status == 'interested').scalar() or 0

    # Meetings booked (global or active month)
    meetings_booked = db.query(func.count(CampaignLog.id))\
                        .filter(CampaignLog.event_type.like('%booking%')).scalar() or 0

    # Recent campaign log events for the live activity feed
    recent_logs = db.query(CampaignLog)\
                    .order_by(CampaignLog.created_at.desc())\
                    .limit(20).all()

    return {
        "total_leads": total_leads,
        "enriched_leads": enriched_leads,
        "emails_sent": emails_sent,
        "opened_count": opened_count,
        "replied_count": replied_count,
        "interested": interested,
        "meetings_booked": meetings_booked,
        "active_month": active_month_number,
        "recent_logs": [
            {
                "id": log.id,
                "cqc_location_id": log.cqc_location_id,
                "event_type": log.event_type,
                "created_at": str(log.created_at) if log.created_at else None
            }
            for log in recent_logs
        ]
    }

@router.get("/outlook/inbox")
def get_outlook_inbox(db: Session = Depends(get_db), limit: int = 50):
    """Returns actual Microsoft Outlook inbox messages filtered for database leads."""
    results = db.query(OutlookMessage, CqcLead)\
                .join(CqcLead, OutlookMessage.lead_id == CqcLead.id)\
                .filter(OutlookMessage.folder == 'inbox')\
                .order_by(OutlookMessage.received_at.desc())\
                .limit(limit).all()
    return [
        {
            "id": msg.id,
            "from": msg.sender_email,
            "fromName": f"{lead.contact_first_name} {lead.contact_last_name}".strip() or "Unknown",
            "company": lead.company_name or "Unknown Company",
            "subject": msg.subject,
            "preview": msg.body[:80] + "..." if len(msg.body) > 80 else msg.body,
            "body": msg.body,
            "intent": lead.campaign_status,
            "receivedAt": msg.received_at.isoformat() if msg.received_at else None
        }
        for msg, lead in results
    ]

@router.get("/outlook/outbox")
def get_outlook_outbox(db: Session = Depends(get_db), limit: int = 50):
    """Returns actual Microsoft Outlook sent (outbox) messages filtered for database leads."""
    results = db.query(OutlookMessage, CqcLead)\
                .join(CqcLead, OutlookMessage.lead_id == CqcLead.id)\
                .filter(OutlookMessage.folder == 'sentitems')\
                .order_by(OutlookMessage.received_at.desc())\
                .limit(limit).all()
    return [
        {
            "id": msg.id,
            "to": msg.recipient_email,
            "toName": f"{lead.contact_first_name} {lead.contact_last_name}".strip() or "Unknown",
            "company": lead.company_name or "Unknown Company",
            "subject": msg.subject,
            "preview": msg.body[:80] + "..." if len(msg.body) > 80 else msg.body,
            "body": msg.body,
            "sentAt": msg.received_at.isoformat() if msg.received_at else None
        }
        for msg, lead in results
    ]

@router.get("/campaigns/months")
def get_campaign_months(db: Session = Depends(get_db)):
    """Returns all campaign months along with their real-time statistics."""
    months = db.query(CampaignMonth).order_by(CampaignMonth.month_number.asc()).all()
    result = []
    for m in months:
        # Leads count for this month
        total_leads = db.query(func.count(CqcLead.id)).filter(CqcLead.campaign_month == m.month_number).scalar() or 0
        
        # Sent emails for this month
        sent = db.query(func.count(CqcLead.id))\
                 .filter(CqcLead.campaign_month == m.month_number, CqcLead.emailed_at.isnot(None))\
                 .scalar() or 0
        
        # Opened emails for this month's leads
        opened = db.query(func.count(CampaignLog.id))\
                   .join(CqcLead, CampaignLog.cqc_location_id == CqcLead.cqc_location_id)\
                   .filter(CqcLead.campaign_month == m.month_number, CampaignLog.event_type == 'email_opened')\
                   .scalar() or 0
                   
        # Replied leads for this month (status not not_started or active)
        replied = db.query(func.count(CqcLead.id))\
                    .filter(
                        CqcLead.campaign_month == m.month_number,
                        CqcLead.campaign_status.notin_(['not_started', 'active'])
                    ).scalar() or 0
                    
        result.append({
            "id": m.month_number,
            "name": m.name or f"Month {m.month_number}",
            "status": m.status,
            "leads": total_leads or m.leads_count,
            "sent": sent,
            "opened": opened,
            "replied": replied,
            "startDate": m.start_date.isoformat() if m.start_date else None,
            "endDate": m.end_date.isoformat() if m.end_date else None,
            "customPrompt": m.custom_prompt
        })
    return result

from pydantic import BaseModel
from fastapi import HTTPException

class PromptUpdateRequest(BaseModel):
    custom_prompt: str

@router.get("/campaigns/{month_number}/prompt")
def get_campaign_prompt(month_number: int, db: Session = Depends(get_db)):
    """Retrieve the custom prompt for a specific campaign."""
    campaign = db.query(CampaignMonth).filter(CampaignMonth.month_number == month_number).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    
    return {"custom_prompt": campaign.custom_prompt}

@router.put("/campaigns/{month_number}/prompt")
def update_campaign_prompt(month_number: int, data: PromptUpdateRequest, db: Session = Depends(get_db)):
    """Update the custom prompt for a specific campaign."""
    campaign = db.query(CampaignMonth).filter(CampaignMonth.month_number == month_number).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    campaign.custom_prompt = data.custom_prompt
    db.commit()
    return {"status": "success", "custom_prompt": campaign.custom_prompt}

@router.delete("/campaigns/{month_number}")
def delete_campaign(month_number: int, db: Session = Depends(get_db)):
    """Delete a campaign and all its associated leads."""
    campaign = db.query(CampaignMonth).filter(CampaignMonth.month_number == month_number).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
        
    # Delete associated leads
    db.query(CqcLead).filter(CqcLead.campaign_month == month_number).delete(synchronize_session=False)
    
    # Delete campaign
    db.delete(campaign)
    db.commit()
    return {"status": "success", "message": f"Campaign {month_number} and its leads deleted successfully."}
