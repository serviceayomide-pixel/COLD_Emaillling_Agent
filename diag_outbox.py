import urllib.parse
from sqlalchemy import create_engine, text
import pandas as pd

password = urllib.parse.quote("Pa44wd12505")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("="*60)
    print("1. CHECKING IF EMAILS WERE SENT")
    print("="*60)
    
    logs = pd.read_sql(text("""
        SELECT cqc_location_id, event_type, created_at 
        FROM campaign_logs 
        ORDER BY created_at DESC 
        LIMIT 5
    """), conn)
    if logs.empty:
        print("No campaign logs found. The worker hasn't sent anything yet.")
    else:
        print(logs.to_string(index=False))
        
    print("\n" + "="*60)
    print("2. CHECKING OUTLOOK MESSAGES TABLE")
    print("="*60)
    
    msgs = pd.read_sql(text("""
        SELECT folder, subject, received_at 
        FROM outlook_messages 
        ORDER BY received_at DESC 
        LIMIT 5
    """), conn)
    if msgs.empty:
        print("No outlook messages found. Webhook hasn't caught anything yet.")
    else:
        print(msgs.to_string(index=False))
