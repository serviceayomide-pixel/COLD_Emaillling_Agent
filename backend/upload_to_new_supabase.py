import urllib.parse
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
import os
import sys

# Use quote instead of quote_plus so the space correctly becomes %20 instead of +
password = urllib.parse.quote(" Pwd15408?z")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

print("Connecting to Supabase Gen122...")
try:
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        pass
    print("Connection successful!")
except Exception as e:
    print(f"Failed to connect: {e}")
    sys.exit(1)

# Import the model to ensure table gets created
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app.models.models import Base, CqcLead

print("Creating tables if they don't exist...")
Base.metadata.create_all(bind=engine)

csv_path = "../cqc_merged_with_emails_final.csv"
print(f"Loading CSV data from {csv_path}...")
df = pd.read_csv(csv_path)

# Ensure NaN values are replaced with None
df = df.where(pd.notnull(df), None)
records = df.to_dict('records')

print(f"Preparing to upsert {len(records)} records into Supabase...")

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
session = SessionLocal()

try:
    batch_size = 1000
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        stmt = insert(CqcLead).values(batch)
        
        update_dict = {
            'company_name': stmt.excluded.company_name,
            'contact_first_name': stmt.excluded.contact_first_name,
            'contact_last_name': stmt.excluded.contact_last_name,
            'contact_email': stmt.excluded.contact_email,
            'phone': stmt.excluded.phone,
            'website_url': stmt.excluded.website_url,
            'service_type': stmt.excluded.service_type,
            'specialisms': stmt.excluded.specialisms,
            'provider_name': stmt.excluded.provider_name,
            'local_authority': stmt.excluded.local_authority,
            'region': stmt.excluded.region
        }
        
        stmt = stmt.on_conflict_do_update(
            index_elements=['cqc_location_id'],
            set_=update_dict
        )
        
        session.execute(stmt)
        session.commit()
        print(f"Successfully processed records {i} to {i+len(batch)}...")

    print("SUCCESS: All 29,475 leads have been uploaded to Gen122 Supabase using SQLAlchemy!")
except Exception as e:
    session.rollback()
    print(f"An error occurred during upload: {e}")
finally:
    session.close()
