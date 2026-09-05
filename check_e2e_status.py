import urllib.parse
from sqlalchemy import create_engine, text
import pandas as pd

password = urllib.parse.quote("Pa44wd12505")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("="*60)
    print("E2E TEST LEADS STATUS")
    print("="*60)
    
    # 1. Check Leads
    leads = pd.read_sql(text("""
        SELECT cqc_location_id, contact_email, campaign_status, sequence_step, emailed_at
        FROM cqc_leads 
        WHERE cqc_location_id LIKE 'TEST-E2E-%'
    """), conn)
    print(leads.to_string(index=False))
    
    print("\n" + "="*60)
    print("CAMPAIGN LOGS (Recent)")
    print("="*60)
    
    # 2. Check Logs
    logs = pd.read_sql(text("""
        SELECT cqc_location_id, event_type, created_at 
        FROM campaign_logs 
        ORDER BY created_at DESC 
        LIMIT 10
    """), conn)
    if logs.empty:
        print("No campaign logs found.")
    else:
        print(logs.to_string(index=False))
        
    print("\n" + "="*60)
    print("OUTLOOK MESSAGES (Recent)")
    print("="*60)
    
    # 3. Check Outlook Messages
    msgs = pd.read_sql(text("""
        SELECT lead_id, folder, subject, received_at 
        FROM outlook_messages 
        ORDER BY received_at DESC 
        LIMIT 10
    """), conn)
    if msgs.empty:
        print("No outlook messages found.")
    else:
        print(msgs.to_string(index=False))
