"""
Database migration: Add linkedin_url column to cqc_leads table.
Run this on the Railway console after deploying:
  python add_linkedin_column.py
"""
import urllib.parse
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    # Fallback for local development
    from dotenv import load_dotenv
    load_dotenv()
    DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    # Check if column already exists
    result = conn.execute(text("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name = 'cqc_leads' AND column_name = 'linkedin_url'
    """))
    
    if result.fetchone():
        print("Column 'linkedin_url' already exists. No migration needed.")
    else:
        conn.execute(text("""
            ALTER TABLE cqc_leads ADD COLUMN linkedin_url VARCHAR(500) DEFAULT NULL
        """))
        conn.commit()
        print("Successfully added 'linkedin_url' column to cqc_leads table.")
