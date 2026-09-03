import sys
import os
from datetime import datetime, timezone

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from app.models.models import CqcLead, CampaignMonth

def safe_inject():
    db = SessionLocal()
    
    # Check if Month 1 is active
    month1 = db.query(CampaignMonth).filter(CampaignMonth.month_number == 1).first()
    if not month1:
        print("Creating Campaign Month 1...")
        month1 = CampaignMonth(
            month_number=1,
            status="active",
            start_date=datetime.now(timezone.utc),
            end_date=datetime.now(timezone.utc), # Will be updated
            leads_count=0
        )
        db.add(month1)
        db.commit()
    elif month1.status != 'active':
        print(f"Setting Campaign Month 1 to active (was {month1.status})...")
        month1.status = 'active'
        db.commit()

    test_emails = [
        'praiseoluu@gmail.com', 'arena6663@gmail.com', 'wuraola.mathew@lmu.edu.ng',
        'billy01@ngcag.org', 'billy02@ngcag.org', 'billy03@ngcag.org', 'billy04@ngcag.org',
        'billy05@ngcag.org', 'billy06@ngcag.org', 'billy07@ngcag.org', 'billy08@ngcag.org',
        'billy09@ngcag.org', 'billy10@ngcag.org', 'billy11@ngcag.org', 'billy12@ngcag.org',
        'billy13@ngcag.org', 'billy14@ngcag.org', 'billy15@ngcag.org'
    ]
    
    print(f"Injecting {len(test_emails)} test leads into the production database...")
    
    for i, email in enumerate(test_emails):
        lead = db.query(CqcLead).filter(CqcLead.contact_email == email).first()
        if not lead:
            lead = CqcLead(
                cqc_location_id=f"TEST-PROD-{i+1000}",
                company_name=f"Test Care Group {i+1}",
                contact_first_name="Test",
                contact_last_name=f"Director {i+1}",
                contact_email=email,
                phone=f"07700900{i:03d}",
                website_url=f"https://testcare{i+1}.co.uk",
                local_authority="Test Authority",
                region="London",
                specialisms="Dementia",
                enrichment_status="enriched",
                campaign_month=1
            )
            db.add(lead)
        
        # Reset them to pristine state
        lead.campaign_status = 'not_started'
        lead.sequence_step = 0
        lead.emailed_at = None
        lead.next_email_date = None
        lead.ai_email_subject = None
        lead.ai_email_body = None
        lead.full_email_sequence = None
        
    db.commit()
    print("✅ Test leads successfully injected and reset! The worker will pick them up now.")

if __name__ == "__main__":
    safe_inject()
