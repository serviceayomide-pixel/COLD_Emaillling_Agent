import urllib.parse
from sqlalchemy import create_engine, text
import pandas as pd

password = urllib.parse.quote("Pa44wd12505")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    print("CHECKING SCRAPED CONTENT FOR TEST LEADS:\n")
    df = pd.read_sql(text("""
        SELECT company_name, 
               CASE WHEN scraped_content IS NULL THEN 'NULL' 
                    WHEN scraped_content = '' THEN 'EMPTY STRING'
                    ELSE 'HAS CONTENT (' || LENGTH(scraped_content) || ' characters)' 
               END as scraped_data_status
        FROM cqc_leads 
        WHERE cqc_location_id LIKE 'TEST-E2E-%'
        LIMIT 5
    """), conn)
    print(df.to_string(index=False))
