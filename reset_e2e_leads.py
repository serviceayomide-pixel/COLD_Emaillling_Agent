import urllib.parse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from backend.app.models.models import CqcLead

password = urllib.parse.quote("Pa44wd12505")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print("=" * 60)
print("RESETTING 16 E2E TEST LEADS")
print("=" * 60)

# Delete existing outlook messages and campaign logs for these test leads so we start completely clean
test_lead_ids = db.execute(text("SELECT id FROM cqc_leads WHERE cqc_location_id LIKE 'TEST-E2E-%'")).fetchall()
if test_lead_ids:
    ids_tuple = tuple(row[0] for row in test_lead_ids)
    if len(ids_tuple) == 1:
        ids_sql = f"({ids_tuple[0]})"
    else:
        ids_sql = str(ids_tuple)
        
    db.execute(text(f"DELETE FROM outlook_messages WHERE lead_id IN {ids_sql}"))
    db.execute(text(f"DELETE FROM campaign_logs WHERE cqc_location_id LIKE 'TEST-E2E-%'"))
    db.commit()

# Reset the leads themselves
updated = db.query(CqcLead).filter(
    CqcLead.cqc_location_id.like("TEST-E2E-%")
).update({
    "campaign_status": "not_started",
    "sequence_step": 0,
    "emailed_at": None,
    "next_email_date": None,
    "ai_email_subject": None,
    "ai_email_body": None,
    "full_email_sequence": None
}, synchronize_session=False)

db.commit()
print(f"Successfully reset {updated} E2E test leads to 0.")
print("The queue is now completely clean!")

db.close()
