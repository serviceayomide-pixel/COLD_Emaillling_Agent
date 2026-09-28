from app.core.database import SessionLocal
from app.models.models import CqcLead
from sqlalchemy import or_, and_

db = SessionLocal()
pending_leads = db.query(CqcLead).filter(
    CqcLead.enrichment_status == 'enriched',
    CqcLead.campaign_month == 2,
    CqcLead.campaign_status == 'not_started'
).count()
print(f"Pending 'not_started' leads for Campaign 2: {pending_leads}")
db.close()
