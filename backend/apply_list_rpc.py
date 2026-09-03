import asyncio
import os
from dotenv import load_dotenv
load_dotenv()
import asyncpg

async def apply_list_rpcs():
    # Connect directly to Postgres on port 5432 (bypass pgbouncer limit for DDL)
    db_url = os.environ.get("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL is not set.")
        return
        
    db_url = db_url.replace("6543", "5432").replace("pgbouncer=true", "")
    conn = await asyncpg.connect(db_url)
    
    try:
        # 1. Inbox Metrics RPC
        print("Creating get_inbox_metrics()...")
        await conn.execute("""
        CREATE OR REPLACE FUNCTION get_inbox_metrics()
        RETURNS json
        LANGUAGE plpgsql
        AS $$
        DECLARE
          result json;
        BEGIN
          SELECT json_build_object(
            'interested', COUNT(*) FILTER (WHERE l.campaign_status = 'interested' OR l.campaign_status = 'booked'),
            'not_interested', COUNT(*) FILTER (WHERE l.campaign_status = 'not interested'),
            'request_more_info', COUNT(*) FILTER (WHERE l.campaign_status = 'request more info'),
            'out_of_office', COUNT(*) FILTER (WHERE l.campaign_status = 'out of office'),
            'wrong_contact', COUNT(*) FILTER (WHERE l.campaign_status = 'wrong contact')
          ) INTO result
          FROM outlook_messages m
          LEFT JOIN cqc_leads l ON m.lead_id = l.id
          WHERE m.folder = 'inbox';
          
          RETURN result;
        END;
        $$;
        """)
        
        # 2. Outbox Metrics RPC
        print("Creating get_outbox_metrics()...")
        await conn.execute("""
        CREATE OR REPLACE FUNCTION get_outbox_metrics()
        RETURNS json
        LANGUAGE plpgsql
        AS $$
        DECLARE
          result json;
        BEGIN
          SELECT json_build_object(
            'total_sent', COUNT(*)
          ) INTO result
          FROM outlook_messages m
          WHERE m.folder = 'sentitems';
          
          RETURN result;
        END;
        $$;
        """)

        # 3. Meetings Metrics RPC
        print("Creating get_meetings_metrics()...")
        await conn.execute("""
        CREATE OR REPLACE FUNCTION get_meetings_metrics()
        RETURNS json
        LANGUAGE plpgsql
        AS $$
        DECLARE
          result json;
        BEGIN
          SELECT json_build_object(
            'upcoming', COUNT(*) FILTER (WHERE start_time >= NOW()),
            'past', COUNT(*) FILTER (WHERE start_time < NOW())
          ) INTO result
          FROM meetings;
          
          RETURN result;
        END;
        $$;
        """)

        print("Successfully created list RPCs!")
        
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(apply_list_rpcs())
