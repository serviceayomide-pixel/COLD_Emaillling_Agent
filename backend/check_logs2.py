from app.core.database import SessionLocal
from app.models.models import CampaignLog, CqcLead
from datetime import timezone

db = SessionLocal()
logs = db.query(CampaignLog, CqcLead).join(CqcLead, CampaignLog.cqc_location_id == CqcLead.cqc_location_id).filter(CampaignLog.event_type.like('sent_email_%')).order_by(CampaignLog.created_at.desc()).limit(5).all()

for log, lead in logs:
    dt = log.created_at.replace(tzinfo=timezone.utc)
    print(f"Event: {log.event_type} | Time: {dt.strftime('%H:%M:%S')} | Campaign: {lead.campaign_month}")
db.close()
