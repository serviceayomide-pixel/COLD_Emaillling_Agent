from app.core.database import SessionLocal
from app.models.models import CampaignLog, CqcLead, CampaignMonth
from datetime import timezone, datetime, timedelta

db = SessionLocal()
now = datetime.now(timezone.utc)
twenty_four_hours_ago = now - timedelta(hours=24)

active_month = db.query(CampaignMonth).filter(CampaignMonth.status == 'active').first()
if active_month:
    count = db.query(CampaignLog).join(CqcLead, CampaignLog.cqc_location_id == CqcLead.cqc_location_id).filter(
        CampaignLog.event_type.like('sent_email_%'),
        CampaignLog.created_at >= twenty_four_hours_ago,
        CqcLead.campaign_month == active_month.month_number
    ).count()
    print(f"Active Month: {active_month.month_number}")
    print(f"Daily Limit: {active_month.daily_limit}")
    print(f"Emails Sent in last 24h: {count}")
else:
    print("No active campaigns.")
db.close()
