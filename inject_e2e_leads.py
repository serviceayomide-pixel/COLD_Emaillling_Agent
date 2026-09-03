import urllib.parse
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os
import random

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
from backend.app.models.models import Base, CqcLead

password = urllib.parse.quote(" Pwd15408?z")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)
Session = sessionmaker(bind=engine)
db = Session()

# Pull 16 real production leads that have real verified domains & emails
# These are the REAL leads we'll clone metadata from (website, company, region etc.)
# but we'll REPLACE the contact email with our test emails
print("=" * 60)
print("FETCHING REAL PRODUCTION DOMAINS FROM DATABASE...")
print("=" * 60)

real_leads = db.query(CqcLead).filter(
    CqcLead.website_url.isnot(None),
    CqcLead.website_url != '',
    CqcLead.contact_email.isnot(None),
    CqcLead.enrichment_status == 'enriched',
    # Exclude already-injected test leads
    CqcLead.cqc_location_id.notlike("TEST-E2E-%")
).order_by(CqcLead.id).limit(16).all()

print(f"\nPulled {len(real_leads)} real production leads with verified domains.")

# Our 16 test emails to inject
TEST_EMAILS = [
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
    "arena6663@gmail.com",
]

# Clean up any previous test leads
deleted = db.query(CqcLead).filter(
    CqcLead.cqc_location_id.like("TEST-E2E-%")
).delete(synchronize_session=False)
db.commit()
print(f"\nCleaned up {deleted} old test leads.")

# Inject new test leads cloned from real production data
leads_to_add = []
for i, (real, test_email) in enumerate(zip(real_leads, TEST_EMAILS)):
    lead = CqcLead(
        # Real metadata from production (Firecrawl & SerpDev will work on these!)
        cqc_location_id=f"TEST-E2E-{str(i+1).zfill(3)}",
        company_name=real.company_name,
        contact_first_name=real.contact_first_name or "Manager",
        contact_last_name=real.contact_last_name or "Director",
        phone=real.phone,
        website_url=real.website_url,           # REAL website for Firecrawl to scrape
        local_authority=real.local_authority,
        region=real.region,
        specialisms=real.specialisms,
        scraped_content=real.scraped_content,   # Re-use any already-scraped content
        
        # Test email — replaces the real contact email
        contact_email=test_email,
        
        # Production-ready statuses — worker will pick these up
        enrichment_status="enriched",
        campaign_status="not_started",
        campaign_month=1,
        sequence_step=0,
    )
    leads_to_add.append(lead)

db.add_all(leads_to_add)
db.commit()

print(f"\nSuccessfully injected {len(leads_to_add)} E2E test leads!")
print("\n--- Test Lead Summary ---")
for lead in leads_to_add:
    print(f"  [{lead.cqc_location_id}] {lead.contact_email}")
    print(f"    Company : {lead.company_name}")
    print(f"    Website : {lead.website_url}")
    print(f"    Region  : {lead.region}")
    print()

print("=" * 60)
print("ALL SET! Production tools will now be used on REAL data:")
print("  - Firecrawl   : Will scrape the REAL care home websites")
print("  - OpenRouter  : Will generate AI emails from real context")
print("  - MS Graph    : Will send emails to your test inboxes")
print("  - Reply flow  : Reply to test emails to trigger AI intent")
print("=" * 60)

db.close()
