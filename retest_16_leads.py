import urllib.parse
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from backend.app.models.models import Base, CqcLead, CampaignLog, OutlookMessage, CampaignMonth

password = urllib.parse.quote("Pa44wd12505")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

print("=" * 60)
print("RESETTING DATABASE & RE-INJECTING 16 TEST LEADS")
print("=" * 60)

# 1. Clear old campaign logs and outlook messages
db.query(CampaignLog).delete()
db.query(OutlookMessage).delete()
db.commit()
print("1. Cleared all campaign_logs and outlook_messages.")

# 2. Clean up any previous test leads
deleted = db.query(CqcLead).filter(
    CqcLead.cqc_location_id.like("TEST-E2E-%")
).delete(synchronize_session=False)
db.commit()
print(f"2. Removed {deleted} previous test leads.")

# 3. Pull 16 real production leads with real websites
real_leads = db.query(CqcLead).filter(
    CqcLead.website_url.isnot(None),
    CqcLead.website_url != '',
    CqcLead.contact_email.isnot(None),
    CqcLead.enrichment_status == 'enriched',
    CqcLead.cqc_location_id.notlike("TEST-E2E-%")
).order_by(CqcLead.id).limit(16).all()

TEST_EMAILS = [
    "arena6663@gmail.com",
    "billy01@ngcag.org",
    "billy02@ngcag.org",
    "billy03@ngcag.org",
    "billy04@ngcag.org",
    "billy05@ngcag.org",
    "billy06@ngcag.org",
    "billy07@ngcag.org",
    "billy08@ngcag.org",
    "billy09@ngcag.org",
    "billy10@ngcag.org",
    "billy11@ngcag.org",
    "billy12@ngcag.org",
    "billy13@ngcag.org",
    "billy14@ngcag.org",
    "billy15@ngcag.org",
]

# 4. Inject 16 fresh leads with test emails
leads_to_add = []
for i, (real, test_email) in enumerate(zip(real_leads, TEST_EMAILS)):
    lead = CqcLead(
        cqc_location_id=f"TEST-E2E-{str(i+1).zfill(3)}",
        company_name=real.company_name,
        contact_first_name=real.contact_first_name or "Manager",
        contact_last_name=real.contact_last_name or "Director",
        phone=real.phone,
        website_url=real.website_url,
        local_authority=real.local_authority,
        region=real.region,
        specialisms=real.specialisms,
        scraped_content=real.scraped_content,
        contact_email=test_email,
        enrichment_status="enriched",
        campaign_status="not_started",
        campaign_month=1,
        sequence_step=0,
        emailed_at=None,
        next_email_date=None,
        full_email_sequence=None,
        ai_email_subject=None,
        ai_email_body=None
    )
    leads_to_add.append(lead)

db.add_all(leads_to_add)
db.commit()
print(f"3. Injected {len(leads_to_add)} fresh test leads (arena6663@gmail.com is Lead #1).")

# 5. Ensure Campaign Month 1 is ACTIVE
month1 = db.query(CampaignMonth).filter(CampaignMonth.month_number == 1).first()
if month1:
    month1.status = 'active'
    db.commit()
print("4. Campaign Month 1 is ACTIVE.")

print("\n" + "=" * 60)
print("RESET COMPLETE!")
print("All 16 test leads are fresh in database:")
for lead in leads_to_add:
    print(f"  - [{lead.cqc_location_id}] {lead.contact_email} ({lead.company_name})")
print("=" * 60)

db.close()
