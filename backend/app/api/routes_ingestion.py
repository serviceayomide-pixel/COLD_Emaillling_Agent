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
    custom_prompt: str = Form(None),
    daily_limit: int = Form(200),
    db: Session = Depends(get_db)
):
    """Upload a CSV file and insert leads into the cqc_leads table as a new campaign."""
    is_excel = file.filename.endswith('.xlsx') or file.filename.endswith('.xls')
    is_csv = file.filename.endswith('.csv')
    
    if not is_csv and not is_excel:
        raise HTTPException(status_code=400, detail="Only CSV and Excel files (.xlsx, .xls) are allowed.")
        
    is_validate = validate_only.lower() == 'true'
    
    if not is_validate and not campaign_name:
        raise HTTPException(status_code=400, detail="campaign_name is required when inserting.")
    
    contents = await file.read()
    
    import pandas as pd
    try:
        if is_excel:
            df = pd.read_excel(io.BytesIO(contents))
        else:
            try:
                df = pd.read_csv(io.BytesIO(contents), encoding='utf-8')
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(contents), encoding='latin-1')
                
        # Fill NaNs with empty string to prevent issues
        df = df.fillna("")
        records = df.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
    
    valid_leads = []
    warnings = []
    
    for row_idx, row in enumerate(records, start=2):
        # Normalize keys for robust matching across different formats
        normalized_row = {str(k).lower().strip().replace(' ', '_'): str(v).strip() for k, v in row.items() if str(k).strip()}
        
        contact_email = normalized_row.get('contact_email', normalized_row.get('email', normalized_row.get('mail', '')))
        
        # Extract name
        contact_fname = normalized_row.get('contact_first_name', normalized_row.get('first_name', ''))
        contact_lname = normalized_row.get('contact_last_name', normalized_row.get('last_name', ''))
        
        raw_name = normalized_row.get('name', '')
        if raw_name and not contact_fname:
            parts = str(raw_name).split(' ', 1)
            contact_fname = parts[0]
            contact_lname = parts[1] if len(parts) > 1 else ''

        # Extract company name
        company_name = normalized_row.get('company_name', normalized_row.get('company', ''))
        
        # If company name is missing, try to get it from the website domain or email domain
        if not company_name:
            website_url = normalized_row.get('website_url', normalized_row.get('website', normalized_row.get('url', normalized_row.get('company_website', ''))))
            if website_url:
                company_name = str(website_url).replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
            elif contact_email and '@' in contact_email:
                domain = contact_email.split('@')[1]
                if domain not in ('gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'gmx.de', 'web.de'):
                    company_name = domain.split('.')[0].capitalize()
        
        # If still no company name, use a fallback
        if not company_name:
            company_name = "Ihr Unternehmen"

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
        custom_prompt=custom_prompt,
        daily_limit=daily_limit,
        status="paused", # User must explicitly resume it
        start_date=now_utc,
        end_date=None, # TBD or ongoing
        leads_count=len(valid_leads)
    )
    db.add(new_campaign)
    db.commit()
    
    from sqlalchemy.dialects.postgresql import insert as pg_insert
    
    inserted_count = 0
    
    # Prepare all lead dictionaries
    leads_to_insert = []
    for row_data in valid_leads:
        normalized_row, company_name, contact_email, contact_fname, contact_lname = row_data
        
        website_url = normalized_row.get('website_url', normalized_row.get('website', normalized_row.get('url', normalized_row.get('company_website', None))))
        if website_url:
            website_url = str(website_url).replace('http://', '').replace('https://', '').strip('/')
            
        cqc_id = normalized_row.get('cqc_location_id', normalized_row.get('location_id', normalized_row.get('id', None)))
        if not cqc_id:
            cqc_id = uuid.uuid4().hex
            
        linkedin_url = normalized_row.get('linkedin_url', normalized_row.get('linkedin', normalized_row.get('linkedin_profile', normalized_row.get('company_linkedin', None))))
        if linkedin_url:
            linkedin_url = str(linkedin_url).strip()
            if linkedin_url and linkedin_url.lower() in ('', 'nan', 'none', 'n/a'):
                linkedin_url = None
            
        leads_to_insert.append({
            'cqc_location_id': str(cqc_id),
            'company_name': str(company_name),
            'website_url': website_url,
            'linkedin_url': linkedin_url,
            'region': str(normalized_row.get('region', '')),
            'local_authority': str(normalized_row.get('local_authority', '')),
            'phone': str(normalized_row.get('phone', normalized_row.get('phone_number', ''))),
            'service_type': str(normalized_row.get('service_type', normalized_row.get('service_types', ''))),
            'specialisms': str(normalized_row.get('specialisms', normalized_row.get('specialisms/services', ''))),
            'provider_name': str(normalized_row.get('provider_name', '')),
            'contact_first_name': str(contact_fname),
            'contact_last_name': str(contact_lname),
            'contact_email': str(contact_email),
            'enrichment_status': 'enriched',
            'campaign_status': 'not_started',
            'campaign_month': next_month_number
        })

    if leads_to_insert:
        batch_size = 500
        for i in range(0, len(leads_to_insert), batch_size):
            batch = leads_to_insert[i:i + batch_size]
            # Perform Bulk Upsert in batches
            stmt = pg_insert(CqcLead).values(batch)
            
            # On conflict (duplicate CQC ID), update the record to use the new campaign and updated contact info
            update_dict = {
                'contact_email': stmt.excluded.contact_email,
                'contact_first_name': stmt.excluded.contact_first_name,
                'contact_last_name': stmt.excluded.contact_last_name,
                'campaign_month': stmt.excluded.campaign_month,
                'campaign_status': 'not_started',
                'enrichment_status': 'enriched',
                'emailed_at': None,
                'next_email_date': None,
                'sequence_step': 0,
                'full_email_sequence': None,
                'ai_email_subject': None,
                'ai_email_body': None
            }
            
            stmt = stmt.on_conflict_do_update(
                index_elements=['cqc_location_id', 'campaign_month'],
                set_=update_dict
            )
            
            db.execute(stmt)
            db.commit()
            
        inserted_count = len(leads_to_insert)
    
    duplicate_count = 0 # No longer skipping duplicates, we seamlessly update them!
            
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
