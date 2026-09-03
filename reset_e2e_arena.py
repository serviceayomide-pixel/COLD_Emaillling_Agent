import urllib.parse
from sqlalchemy import create_engine, text
from datetime import datetime, timezone

password = urllib.parse.quote("Pa44wd12505")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=" * 60)
    print("RESETTING DATABASE FOR ARENA6663 E2E TEST")
    print("=" * 60)

    # 1. Clear campaign logs
    conn.execute(text("DELETE FROM campaign_logs"))
    print("1. Cleared all campaign_logs.")

    # 2. Clear outlook messages
    conn.execute(text("DELETE FROM outlook_messages"))
    print("2. Cleared all outlook_messages.")

    # 3. Reset all test leads back to fresh state
    conn.execute(text("""
        UPDATE cqc_leads 
        SET 
            campaign_status = 'not_started',
            sequence_step = 0,
            emailed_at = NULL,
            next_email_date = NULL,
            ai_email_subject = NULL,
            ai_email_body = NULL,
            full_email_sequence = NULL,
            campaign_month = 1,
            enrichment_status = 'enriched'
        WHERE cqc_location_id LIKE 'TEST-E2E-%'
    """))
    print("3. Reset all 16 TEST-E2E leads to 'not_started' in Month 1.")

    # 4. Make sure arena6663@gmail.com is prioritized (lead TEST-E2E-001)
    conn.execute(text("""
        UPDATE cqc_leads
        SET contact_email = 'arena6663@gmail.com',
            contact_first_name = 'Matthew',
            contact_last_name = 'Olu',
            company_name = 'Test Care Home (Arena)'
        WHERE cqc_location_id = 'TEST-E2E-001'
    """))
    print("4. Set TEST-E2E-001 contact email to arena6663@gmail.com (First in line!).")

    # 5. Ensure Campaign Month 1 is ACTIVE
    conn.execute(text("""
        UPDATE campaign_months
        SET status = 'active'
        WHERE month_number = 1
    """))
    print("5. Campaign Month 1 is set to ACTIVE.")

    conn.commit()

    print("\n" + "=" * 60)
    print("ALL DONE! arena6663@gmail.com is #1 in line.")
    print("Worker will pick up arena6663@gmail.com on its very next 1-minute run!")
    print("=" * 60)
