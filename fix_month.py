import urllib.parse
from sqlalchemy import create_engine, text

password = urllib.parse.quote(" Pwd15408?z")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    print("Calibrating Campaign Months...")
    
    # 1. Fix Month 1 (Active)
    conn.execute(text("UPDATE campaign_months SET leads_count = 1000, status = 'active' WHERE month_number = 1"))
    
    # 2. Assign exactly 1,000 Enriched leads to Month 1
    conn.execute(text("""
        UPDATE cqc_leads 
        SET campaign_month = 1 
        WHERE id IN (
            SELECT id FROM cqc_leads 
            WHERE enrichment_status = 'enriched' 
            AND campaign_month IS NULL 
            ORDER BY id ASC 
            LIMIT 1000
        )
    """))

    # 3. Create Month 2 (Queued)
    conn.execute(text("INSERT INTO campaign_months (month_number, status, leads_count) VALUES (2, 'queued', 1000) ON CONFLICT (month_number) DO NOTHING"))
    
    # 4. Assign the next 1,000 Enriched leads to Month 2
    conn.execute(text("""
        UPDATE cqc_leads 
        SET campaign_month = 2 
        WHERE id IN (
            SELECT id FROM cqc_leads 
            WHERE enrichment_status = 'enriched' 
            AND campaign_month IS NULL 
            ORDER BY id ASC 
            LIMIT 1000
        )
    """))
    
    conn.commit()
    print("Month 1 (Active) and Month 2 (Queued) are perfectly calibrated!")
