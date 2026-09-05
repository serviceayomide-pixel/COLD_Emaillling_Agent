import urllib.parse
from sqlalchemy import create_engine, text

password = urllib.parse.quote(" Pwd15408?z")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    print("=" * 50)
    print("SUPABASE REALTIME PUBLICATION CHECK")
    print("=" * 50)
    
    result = conn.execute(text("""
        SELECT schemaname, tablename 
        FROM pg_publication_tables 
        WHERE pubname = 'supabase_realtime'
        ORDER BY tablename;
    """))
    
    realtime_tables = result.fetchall()
    print(f"\nTables with Realtime ENABLED ({len(realtime_tables)}):")
    for row in realtime_tables:
        print(f"  [OK] {row[0]}.{row[1]}")
    
    print("\n--- Cross-check against app tables ---")
    needed = ['cqc_leads', 'campaign_logs', 'campaign_months', 'meetings', 'outlook_messages']
    enabled = [row[1] for row in realtime_tables]
    
    for table in needed:
        if table in enabled:
            print(f"  [OK] {table} -- Realtime ON")
        else:
            print(f"  [MISSING] {table} -- Realtime NOT ENABLED!")
