import urllib.parse
from sqlalchemy import create_engine, text
import os

password = urllib.parse.quote(" Pwd15408?z")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    print("Fixing NaN strings to actual NULLs...")
    
    # Fix contact_email
    conn.execute(text("UPDATE cqc_leads SET contact_email = NULL WHERE contact_email = 'NaN'"))
    
    # Fix phone numbers (they were uploaded as floats like '1234567.0' or 'NaN')
    conn.execute(text("UPDATE cqc_leads SET phone = NULL WHERE phone = 'NaN'"))
    conn.execute(text("UPDATE cqc_leads SET phone = REPLACE(phone, '.0', '') WHERE phone LIKE '%.0'"))
    
    # Fix other string columns
    columns = ['company_name', 'contact_first_name', 'contact_last_name', 'website_url', 'service_type', 'specialisms', 'provider_name', 'local_authority', 'region']
    
    for col in columns:
        conn.execute(text(f"UPDATE cqc_leads SET {col} = NULL WHERE {col} = 'NaN'"))
    
    conn.commit()
    print("Database perfectly cleaned!")
