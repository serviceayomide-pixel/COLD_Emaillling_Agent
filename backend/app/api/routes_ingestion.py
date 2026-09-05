from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import csv
import io
import uuid
from datetime import datetime, timezone
from app.core.database import get_db
from app.models.models import CqcLead, CampaignMonth

router = APIRouter()

@router.post("/upload-csv")
async def upload_csv(
    file: UploadFile = File(...), 
    validate_only: str = Form("false"),
    campaign_name: str = Form(None),
    db: Session = Depends(get_db)
):
    """Upload a CSV file and insert leads into the cqc_leads table as a new campaign."""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed.")
        
    is_validate = validate_only.lower() == 'true'
    
    if not is_validate and not campaign_name:
        raise HTTPException(status_code=400, detail="campaign_name is required when inserting.")
    
    contents = await file.read()
    try:
        csv_text = contents.decode('utf-8')
    except UnicodeDecodeError:
        csv_text = contents.decode('latin-1', errors='ignore')
        
    csv_reader = csv.DictReader(io.StringIO(csv_text))
    
    valid_leads = []
    warnings = []
    
    for row_idx, row in enumerate(csv_reader, start=2):
        # Normalize keys for robust matching across different CSV formats
        normalized_row = {k.lower().strip().replace(' ', '_'): v.strip() if isinstance(v, str) else v for k, v in row.items() if k}
        
        # Support both 'company name', 'name', and 'company_name'
        company_name = normalized_row.get('company_name', normalized_row.get('name', ''))
        if not company_name:
            continue
            
        contact_email = normalized_row.get('contact_email', normalized_row.get('email', ''))
        
        # Identify lead by name for warnings
        contact_fname = normalized_row.get('contact_first_name', normalized_row.get('first_name', ''))
        contact_lname = normalized_row.get('contact_last_name', normalized_row.get('last_name', ''))
        display_name = f"{contact_fname} {contact_lname}".strip() or company_name
        
        if not contact_email:
            warnings.append(f"Row {row_idx} ({display_name}): Missing email address. This lead will be skipped.")
            continue
            
        valid_leads.append((normalized_row, company_name, contact_email, contact_fname, contact_lname))
        
    if is_validate:
        return {
            "status": "success",
            "valid_count": len(valid_leads),
            "warnings": warnings,
            "filename": file.filename
        }
        
    # Insert mode
    if len(valid_leads) == 0:
        raise HTTPException(status_code=400, detail="No valid leads with emails found in CSV.")
        
    # 1. Create new campaign month
    # Get highest month_number
    highest_month = db.query(CampaignMonth).order_by(CampaignMonth.month_number.desc()).first()
    next_month_number = (highest_month.month_number + 1) if highest_month else 1
    
    now_utc = datetime.now(timezone.utc)
    new_campaign = CampaignMonth(
        month_number=next_month_number,
        name=campaign_name,
        source_file=file.filename,
        status="paused", # User must explicitly resume it
        start_date=now_utc,
        end_date=None, # TBD or ongoing
        leads_count=len(valid_leads)
    )
    db.add(new_campaign)
    db.commit()
    
    inserted_count = 0
    duplicate_count = 0
    
    for row_data in valid_leads:
        normalized_row, company_name, contact_email, contact_fname, contact_lname = row_data
        
        website_url = normalized_row.get('website_url', normalized_row.get('website', normalized_row.get('url', None)))
        if website_url:
            website_url = website_url.replace('http://', '').replace('https://', '').strip('/')
            
        cqc_id = normalized_row.get('cqc_location_id', normalized_row.get('location_id', normalized_row.get('id', None)))
        if not cqc_id:
            cqc_id = uuid.uuid4().hex
            
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
            contact_first_name=contact_fname,
            contact_last_name=contact_lname,
            contact_email=contact_email,
            enrichment_status='enriched', # They already have emails!
            campaign_status='not_started',
            campaign_month=next_month_number
        )
        
        db.add(lead)
        try:
            db.commit()
            inserted_count += 1
        except IntegrityError:
            db.rollback()
            # If duplicate cqc_location_id, we just update it
            existing_lead = db.query(CqcLead).filter(CqcLead.cqc_location_id == cqc_id).first()
            if existing_lead:
                existing_lead.contact_email = contact_email
                existing_lead.contact_first_name = contact_fname
                existing_lead.contact_last_name = contact_lname
                existing_lead.campaign_month = next_month_number # Move to the new campaign!
                existing_lead.campaign_status = 'not_started'
                existing_lead.enrichment_status = 'enriched'
                try:
                    db.commit()
                    inserted_count += 1 # Technically updated
                except:
                    db.rollback()
                    duplicate_count += 1
            else:
                duplicate_count += 1
            
    # Update total count
    new_campaign.leads_count = inserted_count
    db.commit()
    
    return {
        "status": "success",
        "campaign_id": next_month_number,
        "inserted": inserted_count,
        "duplicates_skipped": duplicate_count,
        "warnings": warnings
    }
