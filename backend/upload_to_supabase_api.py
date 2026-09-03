import os
import sys
import pandas as pd
from dotenv import load_dotenv
from supabase import create_client, Client
import math

# Load env variables from backend/.env
load_dotenv('.env')

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")

if not url or not key:
    print("ERROR: Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE_KEY in .env")
    sys.exit(1)

print("Connecting to Supabase via REST API...")
supabase: Client = create_client(url, key)

csv_path = "../cqc_merged_with_emails_final.csv"
print(f"Loading CSV data from {csv_path}...")
df = pd.read_csv(csv_path)

# Ensure NaN values are replaced with None for JSON serialization
df = df.replace({float('nan'): None})

# Convert to list of dicts
records = df.to_dict('records')

print(f"Preparing to upsert {len(records)} records into Supabase...")

# Supabase REST API has a payload limit, so we batch them (1000 is safe)
batch_size = 1000
total_batches = math.ceil(len(records) / batch_size)

for i in range(total_batches):
    start_idx = i * batch_size
    batch = records[start_idx : start_idx + batch_size]
    
    # We use upsert to insert new rows or update existing ones based on cqc_location_id
    try:
        response = supabase.table("cqc_leads").upsert(
            batch, 
            on_conflict="cqc_location_id",
            ignore_duplicates=False # We want it to update existing records with the new names/emails
        ).execute()
        print(f"Successfully processed batch {i+1}/{total_batches}...")
    except Exception as e:
        print(f"Error on batch {i+1}: {e}")

print("SUCCESS: Upload completed via Supabase API!")
