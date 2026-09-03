import os
import sys
import pandas as pd
from dotenv import load_dotenv

# Load env variables from backend/.env
load_dotenv('.env')

# Add backend to path so we can import app modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import insert
from app.models.models import CqcLead

# Get DB URL from env
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not found in .env")
    sys.exit(1)

print(f"Connecting to database...")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

csv_path = "../cqc_merged_with_emails_final.csv"
print(f"Loading CSV data from {csv_path}...")
df = pd.read_csv(csv_path)

# Ensure NaN values are replaced with None for SQLAlchemy
df = df.where(pd.notnull(df), None)

# Convert to list of dicts
records = df.to_dict('records')

print(f"Preparing to upsert {len(records)} records into Supabase...")

session = SessionLocal()
try:
    # We will do this in batches of 1000 to be safe and fast
    batch_size = 1000
    for i in range(0, len(records), batch_size):
        batch = records[i:i+batch_size]
        
        # Build the insert statement
        stmt = insert(CqcLead).values(batch)
        
        # Setup the ON CONFLICT DO UPDATE part
        # We conflict on cqc_location_id (which is unique)
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
        
        # Execute the batch
        session.execute(stmt)
        session.commit()
        print(f"Successfully processed batch {i} to {i+len(batch)}...")

    print("SUCCESS: All records have been successfully uploaded/updated in Supabase!")
except Exception as e:
    session.rollback()
    print(f"An error occurred: {e}")
finally:
    session.close()

