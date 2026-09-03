import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Ensure backend folder is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

load_dotenv()

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models.models import CampaignMonth, OutlookMessage, CqcLead

def transition_month():
    print("Transitioning to the next queued campaign month...")
    
    db_url = os.environ.get("DATABASE_URL")
    if db_url and ":6543/" in db_url:
        db_url = db_url.replace(":6543/", ":5432/")
            
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    db = SessionLocal()
    try:
        # Find active month
        active_month = db.query(CampaignMonth).filter(CampaignMonth.status == "active").first()
        
        # Find next queued month
        queued_month = db.query(CampaignMonth).filter(CampaignMonth.status == "queued").order_by(CampaignMonth.month_number).first()
        
        if not queued_month:
            print("Error: No queued campaign month found. Cannot transition.")
            return

        if active_month:
            print(f"Marking Month {active_month.month_number} as 'completed'...")
            active_month.status = "completed"
            
            print(f"Deleting inbox/outbox messages from Month {active_month.month_number} to refresh views...")
            # The user requested to delete inbox and outbox messages for the old campaign to "refresh" it
            db.execute(
                text("DELETE FROM outlook_messages WHERE lead_id IN (SELECT id FROM cqc_leads WHERE campaign_month = :old_month)"),
                {"old_month": active_month.month_number}
            )

        print(f"Marking Month {queued_month.month_number} as 'active'...")
        queued_month.status = "active"
        queued_month.start_date = datetime.utcnow()
        queued_month.end_date = queued_month.start_date + timedelta(days=30)
        
        db.commit()
        print(f"Successfully transitioned to Month {queued_month.month_number}.")
        
    except Exception as e:
        db.rollback()
        print(f"Error transitioning month: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    transition_month()
