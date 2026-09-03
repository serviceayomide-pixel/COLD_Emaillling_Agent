import os
import sys
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

# Ensure backend folder is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from sqlalchemy import text
from app.core.database import engine, Base, SessionLocal
from app.models.models import CqcLead, CampaignMonth

def run_migrations():
    print("Starting database migration...")
    
    # 1. Add column to cqc_leads if not exists
    with engine.begin() as conn:
        print("Checking/adding campaign_month column to cqc_leads...")
        # Check if column exists
        try:
            conn.execute(text("ALTER TABLE cqc_leads ADD COLUMN IF NOT EXISTS campaign_month INTEGER;"))
            print("  campaign_month column checked/created successfully.")
        except Exception as e:
            print(f"  Error checking/creating campaign_month column: {e}")

    # 2. Create tables that don't exist yet
    print("Creating tables (campaign_months, outlook_messages)...")
    Base.metadata.create_all(bind=engine)
    print("  Tables checked/created successfully.")

    # 3. Setup Month 1 if it doesn't exist yet
    db = SessionLocal()
    try:
        month1 = db.query(CampaignMonth).filter(CampaignMonth.month_number == 1).first()
        if not month1:
            print("Initializing Month 1 Campaign...")
            now_utc = datetime.now(timezone.utc)
            month1 = CampaignMonth(
                month_number=1,
                status="active",
                start_date=now_utc,
                end_date=now_utc + timedelta(days=30),
                leads_count=1000
            )
            db.add(month1)
            db.commit()
            print("  Month 1 Campaign initialized as active.")
            
            # Map first 1,000 leads in the DB to Month 1
            print("Mapping existing leads to Month 1...")
            # Set all leads with no campaign_month to Month 1 (we currently have 1,000 leads in total)
            leads_updated = db.query(CqcLead).filter(CqcLead.campaign_month.is_(None)).update(
                {CqcLead.campaign_month: 1}, synchronize_session=False
            )
            db.commit()
            print(f"  Mapped {leads_updated} leads to Month 1.")
        else:
            print("Month 1 Campaign already exists in DB.")
    except Exception as e:
        db.rollback()
        print(f"Error during month initialization: {e}")
    finally:
        db.close()
        
    print("Migration finished successfully.")

if __name__ == "__main__":
    run_migrations()
