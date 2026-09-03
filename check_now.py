import urllib.parse
from sqlalchemy import create_engine, text
import pandas as pd

password = urllib.parse.quote("Pa44wd12505")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=== TEST LEADS STATUS ===")
    df_leads = pd.read_sql(text("""
        SELECT cqc_location_id, contact_email, campaign_status, sequence_step, emailed_at, next_email_date, campaign_month
        FROM cqc_leads
        WHERE cqc_location_id LIKE 'TEST-E2E-%'
        ORDER BY id ASC
        LIMIT 5
    """), conn)
    print(df_leads.to_string(index=False))

    print("\n=== RECENT CAMPAIGN LOGS ===")
    df_logs = pd.read_sql(text("""
        SELECT cqc_location_id, event_type, created_at
        FROM campaign_logs
        ORDER BY created_at DESC
        LIMIT 5
    """), conn)
    if df_logs.empty:
        print("No campaign logs yet.")
    else:
        print(df_logs.to_string(index=False))

    print("\n=== OUTLOOK MESSAGES ===")
    df_msgs = pd.read_sql(text("""
        SELECT folder, subject, sender_email, recipient_email, received_at
        FROM outlook_messages
        ORDER BY received_at DESC
        LIMIT 5
    """), conn)
    if df_msgs.empty:
        print("No outlook messages yet.")
    else:
        print(df_msgs.to_string(index=False))
