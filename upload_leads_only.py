import sys
import os
import uuid
import pandas as pd
from dotenv import load_dotenv

sys.path.append(os.path.abspath("backend"))
load_dotenv(os.path.abspath("backend/.env"))

from app.core.database import SessionLocal
from app.models.models import CqcLead

db = SessionLocal()
try:
    df = pd.read_csv("602 marketing manager for animation company(Contacts).csv")
    new_leads = []
    
    for idx, row in df.iterrows():
        email = str(row.get('Email', '')).strip()
        if pd.isna(email) or not email or email.lower() == 'nan':
            continue
            
        first_name = str(row.get('First Name', '')).strip()
        last_name = str(row.get('Last Name', '')).strip()
        company = str(row.get('Company', '')).strip()
        job_title = str(row.get('Job Title', '')).strip()
        industry = str(row.get('Industry', '')).strip()
        linkedin = str(row.get('Company LinkedIn Profile', '')).strip()
        
        # We must set cqc_location_id since it is required & unique. We can use a generated UUID
        location_id = "L-" + str(uuid.uuid4())[:8].upper()
            
        new_lead = CqcLead(
            cqc_location_id=location_id,
            contact_first_name=first_name if first_name.lower() != 'nan' else "",
            contact_last_name=last_name if last_name.lower() != 'nan' else "",
            contact_email=email,
            company_name=company if company and company.lower() != 'nan' else "Unknown",
            specialisms=job_title if job_title and job_title.lower() != 'nan' else None,
            service_type=industry if industry and industry.lower() != 'nan' else None,
            website_url=linkedin if linkedin and linkedin.lower() != 'nan' else None, # Store linkedin temporarily in website_url
            sequence_step=0,
            campaign_status="not_started",
            enrichment_status="pending",
            campaign_month=1
        )
        new_leads.append(new_lead)
        
    if new_leads:
        db.add_all(new_leads)
        db.commit()
        print(f"Successfully uploaded {len(new_leads)} leads to the database.")
    else:
        print("No valid leads found.")

except Exception as e:
    print("Error:", e)
finally:
    db.close()
