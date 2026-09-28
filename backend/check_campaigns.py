from app.core.database import SessionLocal
from app.models.models import CampaignMonth

db = SessionLocal()
campaigns = db.query(CampaignMonth).all()
for c in campaigns:
    print(f"Month: {c.month_number} | Status: {c.status} | Limit: {c.daily_limit}")
db.close()
