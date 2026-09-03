import urllib.parse
from sqlalchemy import create_engine, text

password = urllib.parse.quote("Pa44wd12505")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("=" * 60)
    print("RESETTING ALL BOOKINGS TO ZERO")
    print("=" * 60)

    # 1. Clear the meetings table
    result_meetings = conn.execute(text("DELETE FROM meetings"))
    print(f"1. Deleted {result_meetings.rowcount} rows from 'meetings' table.")

    # 2. Reset any leads with 'booked' campaign_status back to 'not_started'
    result_leads = conn.execute(text("""
        UPDATE cqc_leads 
        SET campaign_status = 'not_started' 
        WHERE campaign_status = 'booked'
    """))
    print(f"2. Reset {result_leads.rowcount} leads from 'booked' to 'not_started'.")

    # 3. Clear any booking logs from campaign_logs if any remained
    result_logs = conn.execute(text("DELETE FROM campaign_logs WHERE event_type LIKE '%meeting%' OR event_type LIKE '%book%'"))
    print(f"3. Cleared {result_logs.rowcount} meeting logs from 'campaign_logs'.")

    conn.commit()

    print("\n" + "=" * 60)
    print("BOOKINGS ARE NOW 100% RESET TO ZERO!")
    print("=" * 60)
