import urllib.parse
from sqlalchemy import create_engine, text

password = urllib.parse.quote(" Pwd15408?z")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    print("Enabling Supabase Realtime for frontend subscriptions...")
    
    # Add tables to the realtime publication
    tables = ['cqc_leads', 'campaign_logs', 'meetings', 'campaign_months', 'outlook_messages']
    
    for table in tables:
        try:
            conn.execute(text(f"ALTER PUBLICATION supabase_realtime ADD TABLE {table};"))
            print(f"Added {table} to realtime publication.")
        except Exception as e:
            # If it's already in the publication, it will throw an error, which we can ignore
            if 'already' in str(e).lower():
                print(f"{table} is already in the publication.")
            else:
                print(f"Error adding {table}: {e}")
                
    conn.commit()
    print("Realtime configuration complete!")
