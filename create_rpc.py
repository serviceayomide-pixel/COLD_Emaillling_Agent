import asyncio
import os
from sqlalchemy import text
from app.core.database import SessionLocal

sql = """
CREATE OR REPLACE FUNCTION get_inbox_metrics()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$$
DECLARE
    result json;
BEGIN
    SELECT json_object_agg(campaign_status, count)
    INTO result
    FROM (
        SELECT campaign_status, count(*) as count
        FROM cqc_leads
        WHERE campaign_status NOT IN ('not_started', 'active', 'finished')
        GROUP BY campaign_status
    ) as stats;
    
    RETURN COALESCE(result, '{}'::json);
END;
$$$;
"""

def run():
    db = SessionLocal()
    try:
        db.execute(text(sql))
        db.commit()
        print("Successfully recreated get_inbox_metrics RPC!")
    except Exception as e:
        print("Error:", e)
    finally:
        db.close()

if __name__ == "__main__":
    run()
