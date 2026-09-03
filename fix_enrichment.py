import urllib.parse
from sqlalchemy import create_engine, text

password = urllib.parse.quote(" Pwd15408?z")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    print("Setting enrichment_status for all 29,475 leads...")
    
    # Set to 'enriched' if they have an email
    conn.execute(text("UPDATE cqc_leads SET enrichment_status = 'enriched' WHERE contact_email IS NOT NULL AND contact_email != ''"))
    
    # Set to 'pending' if they do NOT have an email
    conn.execute(text("UPDATE cqc_leads SET enrichment_status = 'pending' WHERE contact_email IS NULL OR contact_email = ''"))
    
    conn.commit()
    print("Successfully updated all statuses!")
