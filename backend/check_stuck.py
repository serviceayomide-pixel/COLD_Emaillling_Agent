import asyncio
from app.core.database import SessionLocal
from app.models.models import CqcLead
from sqlalchemy import or_
from datetime import timezone, datetime

async def check():
    db = SessionLocal()
    now_utc = datetime.now(timezone.utc)
    leads = db.query(CqcLead).filter(
        CqcLead.campaign_status.in_(['not_started', 'active']),
        CqcLead.campaign_month == 2,
        or_(
            CqcLead.next_email_date <= now_utc,
            CqcLead.next_email_date.is_(None)
        )
    ).order_by(CqcLead.id.asc()).limit(2).all()
    
    for lead in leads:
        print(f"Lead ID: {lead.id} | Email: {lead.contact_email} | Website: {lead.website_url}")
        
    db.close()

asyncio.run(check())
