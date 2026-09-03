import os
import sqlalchemy

db_url = os.environ.get('DATABASE_URL')
if db_url and '6543' in db_url:
    db_url = db_url.replace('6543', '5432')

engine = sqlalchemy.create_engine(db_url)

with engine.connect() as conn:
    print("Checking campaign logs in Testing DB:")
    try:
        res = conn.execute(sqlalchemy.text("SELECT * FROM campaign_logs ORDER BY created_at DESC LIMIT 10"))
        for row in res:
            print(row)
    except Exception as e:
        print("Query Failed:", e)
