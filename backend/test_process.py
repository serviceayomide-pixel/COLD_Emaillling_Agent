import asyncio
from app.core.database import SessionLocal
from app.worker import process_lead
from app.models.models import CqcLead

async def test():
    db = SessionLocal()
    lead = db.query(CqcLead).filter(CqcLead.id == 4759).first()
    if lead:
        print(f"Testing lead: {lead.contact_email}")
        result = await process_lead(db, lead)
        print(f"Result: {result}")
    db.close()

asyncio.run(test())
