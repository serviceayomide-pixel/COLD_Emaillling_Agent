import urllib.parse
from sqlalchemy import create_engine, text

password = urllib.parse.quote("Pa44wd12505")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("Wiping scraped content for test leads to force Firecrawl...")
    result = conn.execute(text("""
        UPDATE cqc_leads 
        SET scraped_content = NULL 
        WHERE cqc_location_id LIKE 'TEST-E2E-%'
    """))
    conn.commit()
    print(f"Cleared scraped data for {result.rowcount} test leads!")
