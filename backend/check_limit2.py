from app.core.database import SessionLocal
from app.models.models import CampaignLog, CqcLead
from datetime import timezone, datetime, timedelta

db = SessionLocal()
now = datetime.now(timezone.utc)
twenty_four_hours_ago = now - timedelta(hours=24)

count = db.query(CampaignLog).join(CqcLead, CampaignLog.cqc_location_id == CqcLead.cqc_location_id).filter(
    CampaignLog.event_type.like('sent_email_%'),
    CampaignLog.created_at >= twenty_four_hours_ago,
    CqcLead.campaign_month == 2
).count()
print(f"Emails Sent for Campaign 2 in last 24h: {count}")
db.close()
