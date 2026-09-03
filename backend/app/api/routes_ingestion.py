from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import csv
import io
from app.core.database import get_db
from app.models.models import CqcLead

router = APIRouter()

@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """Upload a CQC CSV file and insert leads into the cqc_leads table."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
    
    contents = await file.read()
    try:
        csv_text = contents.decode('utf-8')
    except UnicodeDecodeError:
        csv_text = contents.decode('latin-1', errors='ignore')
        
    csv_reader = csv.DictReader(io.StringIO(csv_text))
    
    inserted_count = 0
    duplicate_count = 0
    
    for row in csv_reader:
        # Normalize keys for robust matching across different CSV formats
        normalized_row = {k.lower().strip().replace(' ', '_'): v.strip() if isinstance(v, str) else v for k, v in row.items() if k}
        
        # Support both 'company name', 'name', and 'company_name'
        company_name = normalized_row.get('company_name', normalized_row.get('name', ''))
        if not company_name:
            continue
            
        # Support both 'website', 'url', and 'website_url'
        website_url = normalized_row.get('website_url', normalized_row.get('website', normalized_row.get('url', None)))
        if website_url:
            website_url = website_url.replace('http://', '').replace('https://', '').strip('/')
            
        # Support 'location id', 'id', and 'cqc_location_id'
        cqc_id = normalized_row.get('cqc_location_id', normalized_row.get('location_id', normalized_row.get('id', None)))
        
        lead = CqcLead(
            cqc_location_id=cqc_id,
            company_name=company_name,
            website_url=website_url,
            region=normalized_row.get('region', ''),
            local_authority=normalized_row.get('local_authority', ''),
            phone=normalized_row.get('phone', normalized_row.get('phone_number', '')),
            service_type=normalized_row.get('service_type', normalized_row.get('service_types', '')),
            specialisms=normalized_row.get('specialisms', normalized_row.get('specialisms/services', '')),
            provider_name=normalized_row.get('provider_name', ''),
            contact_first_name=normalized_row.get('contact_first_name', ''),
            contact_last_name=normalized_row.get('contact_last_name', ''),
            contact_email=normalized_row.get('contact_email', ''),
            enrichment_status='pending',
            campaign_status='not_started'
        )
        
        db.add(lead)
        try:
            db.commit()
            inserted_count += 1
        except IntegrityError:
            db.rollback()
            # Try to update the existing record if it's a duplicate but missing new rich data
            existing_lead = db.query(CqcLead).filter(CqcLead.cqc_location_id == cqc_id).first()
            if existing_lead:
                updated = False
                if not existing_lead.contact_email and lead.contact_email:
                    existing_lead.contact_email = lead.contact_email
                    updated = True
                if not existing_lead.contact_first_name and lead.contact_first_name:
                    existing_lead.contact_first_name = lead.contact_first_name
                    updated = True
                if not existing_lead.contact_last_name and lead.contact_last_name:
                    existing_lead.contact_last_name = lead.contact_last_name
                    updated = True
                
                if updated:
                    try:
                        db.commit()
                    except:
                        db.rollback()
            
            duplicate_count += 1
            
    return {
        "status": "success",
        "inserted": inserted_count,
        "duplicates_skipped_or_updated": duplicate_count
    }
