from app.core.database import SessionLocal
from app.models.models import CqcLead

db = SessionLocal()
emails_to_remove = [
    'gerhard.sturm@severin.com',
    'andre.bubolz@tkd-kabel.de',
    'JRudel@dreiturm.de',
    'sigurd.schuetz@rhewum.com'
]

for email in emails_to_remove:
    lead = db.query(CqcLead).filter(CqcLead.contact_email.ilike(email)).first()
    if lead:
        print(f"Removing {lead.contact_email} (Current status: {lead.campaign_status})")
        lead.campaign_status = 'bounced' # Or not interested, setting to bounced removes from pipeline
    else:
        print(f"Lead not found: {email}")

db.commit()
db.close()
