import os
import sys
sys.path.append(os.path.join(os.getcwd(), "backend"))
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(os.path.join("backend", ".env"))
db_url = os.environ.get("DATABASE_URL")
if "6543" in db_url:
    db_url = db_url.replace("6543", "5432")

engine = create_engine(db_url)

with engine.connect() as conn:
    result = conn.execute(text("SELECT contact_email, campaign_status, next_email_date FROM cqc_leads WHERE campaign_status IN ('out of office', 'not interested', 'interested', 'replied') OR next_email_date IS NULL ORDER BY emailed_at DESC LIMIT 10"))
    rows = result.fetchall()
    print("--- RECENT LEAD REPLIES ---")
    for row in rows:
        print(f"Email: {row[0]}")
        print(f"Status: {row[1]}")
        print(f"Next Email Date: {row[2]}")
        print("-")
