import urllib.parse
from sqlalchemy import create_engine, text

password = urllib.parse.quote("Pa44wd12505")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=" * 60)
    print("RESETTING ALL DASHBOARD METRICS")
    print("=" * 60)

    # 1. Clear all campaign logs (this drives the 'Sent' metric, charts, and 'opened' stats)
    result_logs = conn.execute(text("DELETE FROM campaign_logs"))
    print(f"Deleted all {result_logs.rowcount} campaign logs (Sent/Opened/Replied history).")

    # 2. Clear all outlook messages (this drives Inbox/Outbox)
    result_msgs = conn.execute(text("DELETE FROM outlook_messages"))
    print(f"Deleted all {result_msgs.rowcount} outlook messages.")
    
    # 3. Reset all lead statuses globally back to fresh state
    # This ensures 'active_leads', 'total_replied_count', 'total_interested_count' go back to 0
    result_leads = conn.execute(text("""
        UPDATE cqc_leads 
        SET 
            campaign_status = 'not_started',
            sequence_step = 0,
            emailed_at = NULL,
            next_email_date = NULL,
            ai_email_subject = NULL,
            ai_email_body = NULL,
            full_email_sequence = NULL
        WHERE campaign_status != 'not_started' 
           OR sequence_step > 0 
           OR emailed_at IS NOT NULL
    """))
    print(f"Reset {result_leads.rowcount} leads back to 'not_started'.")

    conn.commit()

    print("\n" + "=" * 60)
    print("DASHBOARD IS NOW 100% CLEAN!")
    print("Expected Dashboard Numbers:")
    print("  Prospects : ~29,491")
    print("  Verified  : ~2,687")
    print("  Sent      : 0")
    print("  Active    : 0")
    print("=" * 60)
