import urllib.parse
from sqlalchemy import create_engine, text

password = urllib.parse.quote(" Pwd15408?z")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    print("Inserting Month 1 into campaign_months...")
    conn.execute(text("INSERT INTO campaign_months (month_number, status, leads_count) VALUES (1, 'active', 29475) ON CONFLICT DO NOTHING"))
    conn.commit()
    print("Done!")
