import os
import sqlalchemy

db_url = os.environ.get('DATABASE_URL')
if db_url and '6543' in db_url:
    db_url = db_url.replace('6543', '5432')

engine = sqlalchemy.create_engine(db_url)

with engine.connect() as conn:
    print("Leads in DB:")
    res = conn.execute(sqlalchemy.text("SELECT id, contact_email, campaign_status, enrichment_status, campaign_month FROM cqc_leads"))
    for row in res:
        print(row)
