import pandas as pd
from app.core.database import SessionLocal
from app.models.models import CqcLead, CampaignMonth

db = SessionLocal()
latest_campaign = db.query(CampaignMonth).order_by(CampaignMonth.month_number.desc()).first()
if latest_campaign:
    print(f"Exporting leads for Campaign Month {latest_campaign.month_number}")
    leads = db.query(CqcLead).filter(CqcLead.campaign_month == latest_campaign.month_number).all()
    
    data = []
    for lead in leads:
        data.append({
            'ID': lead.id,
            'First Name': lead.contact_first_name,
            'Last Name': lead.contact_last_name,
            'Email': lead.contact_email,
            'Company': lead.company_name,
            'Website': lead.website_url,
            'LinkedIn': lead.linkedin_url
        })
        
    df = pd.DataFrame(data)
    df.to_csv('C:/Users/MATT/.gemini/antigravity/brain/17c9578f-a592-4b7e-b291-e5ae2159546e/scratch/uploaded_681_leads.csv', index=False)
    print(f"Exported {len(data)} leads to scratch folder.")
else:
    print("No campaigns found.")
db.close()
