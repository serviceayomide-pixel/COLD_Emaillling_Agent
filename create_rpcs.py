import urllib.parse
from sqlalchemy import create_engine, text

password = urllib.parse.quote(" Pwd15408?z")
DATABASE_URL = f"postgresql://postgres.rojuifpeywxpflaimvks:{password}@aws-0-eu-west-1.pooler.supabase.com:5432/postgres"

engine = create_engine(DATABASE_URL)
with engine.connect() as conn:
    print("Creating Postgres RPC Functions...")

    # 1. get_global_dashboard_metrics
    conn.execute(text("""
    CREATE OR REPLACE FUNCTION get_global_dashboard_metrics()
    RETURNS json AS $$
    DECLARE
        result json;
    BEGIN
        SELECT json_build_object(
            'total_leads', (SELECT COUNT(*) FROM cqc_leads),
            'verified_leads', (SELECT COUNT(*) FROM cqc_leads WHERE enrichment_status = 'enriched'),
            'total_emails_sent', (SELECT COUNT(*) FROM cqc_leads WHERE emailed_at IS NOT NULL),
            'total_emails_opened', (SELECT COUNT(*) FROM campaign_logs WHERE event_type = 'email_opened'),
            'total_replied_count', (SELECT COUNT(*) FROM cqc_leads WHERE campaign_status NOT IN ('not_started', 'active')),
            'total_interested_count', (SELECT COUNT(*) FROM cqc_leads WHERE campaign_status = 'interested'),
            'meetings_booked', (SELECT COUNT(*) FROM campaign_logs WHERE event_type LIKE '%booking%'),
            'chart_data', '[]'::json
        ) INTO result;
        RETURN result;
    END;
    $$ LANGUAGE plpgsql;
    """))

    # 2. get_campaign_month_metrics
    conn.execute(text("""
    CREATE OR REPLACE FUNCTION get_campaign_month_metrics(target_month int)
    RETURNS json AS $$
    DECLARE
        result json;
    BEGIN
        SELECT json_build_object(
            'total_leads', (SELECT COUNT(*) FROM cqc_leads WHERE campaign_month = target_month),
            'total_emails_sent', (SELECT COUNT(*) FROM cqc_leads WHERE campaign_month = target_month AND emailed_at IS NOT NULL),
            'total_replied_count', (SELECT COUNT(*) FROM cqc_leads WHERE campaign_month = target_month AND campaign_status NOT IN ('not_started', 'active'))
        ) INTO result;
        RETURN result;
    END;
    $$ LANGUAGE plpgsql;
    """))
    
    # 3. get_analytics_metrics
    conn.execute(text("""
    CREATE OR REPLACE FUNCTION get_analytics_metrics() RETURNS json AS $$
    BEGIN RETURN get_global_dashboard_metrics(); END;
    $$ LANGUAGE plpgsql;
    """))

    # 4. get_inbox_metrics
    conn.execute(text("""
    CREATE OR REPLACE FUNCTION get_inbox_metrics() RETURNS json AS $$
    BEGIN RETURN json_build_object('total', (SELECT COUNT(*) FROM outlook_messages WHERE folder = 'inbox')); END;
    $$ LANGUAGE plpgsql;
    """))

    # 5. get_outbox_metrics
    conn.execute(text("""
    CREATE OR REPLACE FUNCTION get_outbox_metrics() RETURNS json AS $$
    BEGIN RETURN json_build_object('total', (SELECT COUNT(*) FROM outlook_messages WHERE folder = 'sentitems')); END;
    $$ LANGUAGE plpgsql;
    """))

    # 6. get_meetings_metrics
    conn.execute(text("""
    CREATE OR REPLACE FUNCTION get_meetings_metrics() RETURNS json AS $$
    BEGIN RETURN json_build_object('total', (SELECT COUNT(*) FROM meetings)); END;
    $$ LANGUAGE plpgsql;
    """))

    conn.commit()
    print("Successfully created all RPC functions!")
