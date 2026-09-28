from app.core.database import SessionLocal
from app.models.models import CampaignLog
from datetime import timezone

db = SessionLocal()
logs = db.query(CampaignLog).filter(CampaignLog.event_type.like('sent_email_%')).order_by(CampaignLog.created_at.desc()).limit(10).all()

for log in logs:
    dt = log.created_at.replace(tzinfo=timezone.utc)
    print(f"Event: {log.event_type} | Time (UTC): {dt.strftime('%Y-%m-%d %H:%M:%S')}")

db.close()
