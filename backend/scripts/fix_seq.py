import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import SessionLocal
from sqlalchemy import text

db = SessionLocal()
try:
    print('Fixing sequence cqc_leads_id_seq...')
    db.execute(text("SELECT setval('cqc_leads_id_seq', (SELECT MAX(id) FROM cqc_leads));"))
    db.commit()
    print('Sequence fixed!')
except Exception as e:
    db.rollback()
    try:
        print('Trying cqc_leads_new_id_seq instead...')
        db.execute(text("SELECT setval('cqc_leads_new_id_seq', (SELECT MAX(id) FROM cqc_leads));"))
        db.commit()
        print('Sequence fixed (new)!')
    except Exception as e2:
        print('Failed again:', e2)
