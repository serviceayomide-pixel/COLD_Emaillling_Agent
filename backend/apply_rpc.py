import os
import sqlalchemy
from dotenv import load_dotenv

load_dotenv()

# We must ensure we connect to the session pooler (port 5432) for DDL
# or we can use the default URL if it works for short statements.
db_url = os.environ.get("DATABASE_URL")
if db_url and "6543" in db_url:
    db_url = db_url.replace("6543", "5432")

engine = sqlalchemy.create_engine(db_url)

sql_dashboard = """
CREATE OR REPLACE FUNCTION get_global_dashboard_metrics()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    total_leads_count int;
    verified_leads_count int;
    active_leads_count int;
    total_emails_sent int;
    total_emails_opened int;
    total_replied_count int;
    total_interested_count int;
    meetings_booked_count int;
    chart_data json;
BEGIN
    SELECT count(*) INTO total_leads_count FROM cqc_leads;
    SELECT count(*) INTO verified_leads_count FROM cqc_leads WHERE enrichment_status = 'enriched';
    SELECT count(*) INTO active_leads_count FROM cqc_leads WHERE campaign_status = 'active';
    
    SELECT count(*) INTO total_emails_sent FROM campaign_logs WHERE event_type = 'email_sent' OR event_type LIKE 'sent_email_%';
    SELECT count(DISTINCT cqc_location_id) INTO total_emails_opened FROM campaign_logs WHERE event_type = 'email_opened';
    
    SELECT count(*) INTO total_replied_count FROM cqc_leads WHERE campaign_status NOT IN ('not_started', 'active') AND emailed_at IS NOT NULL;
    
    -- Include 'booked' in 'interested' because anyone who booked was also interested!
    SELECT count(*) INTO total_interested_count FROM cqc_leads WHERE campaign_status IN ('interested', 'booked');
    
    SELECT count(*) INTO meetings_booked_count FROM meetings WHERE status = 'ACCEPTED';
    
    SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json) INTO chart_data
    FROM (
        SELECT 
            to_char(g.day, 'Dy DD') as date,
            COALESCE(SUM(CASE WHEN l.event_type = 'email_sent' OR l.event_type LIKE 'sent_email_%' THEN 1 ELSE 0 END), 0) as sent,
            COALESCE(COUNT(DISTINCT CASE WHEN l.event_type = 'email_opened' THEN l.cqc_location_id ELSE NULL END), 0) as opened
        FROM generate_series(
            date_trunc('day', now() - interval '6 days'),
            date_trunc('day', now()),
            interval '1 day'
        ) g(day)
        LEFT JOIN campaign_logs l ON date_trunc('day', l.created_at) = g.day
        GROUP BY g.day
        ORDER BY g.day ASC
    ) t;

    RETURN json_build_object(
        'total_leads', total_leads_count,
        'verified_leads', verified_leads_count,
        'active_leads', active_leads_count,
        'total_emails_sent', total_emails_sent,
        'total_emails_opened', total_emails_opened,
        'total_replied_count', total_replied_count,
        'total_interested_count', total_interested_count,
        'meetings_booked', meetings_booked_count,
        'chart_data', chart_data
    );
END;
$$;
"""

sql_campaigns = """
CREATE OR REPLACE FUNCTION get_campaign_month_metrics(target_month int)
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    leads_count int;
    sent_count int;
    opened_count int;
    replied_count int;
BEGIN
    SELECT count(*) INTO leads_count FROM cqc_leads WHERE campaign_month = target_month;
    SELECT count(*) INTO sent_count FROM cqc_leads WHERE campaign_month = target_month AND emailed_at IS NOT NULL;
    SELECT count(*) INTO replied_count FROM cqc_leads WHERE campaign_month = target_month AND campaign_status NOT IN ('not_started', 'active');
    
    SELECT count(DISTINCT l.cqc_location_id) INTO opened_count
    FROM campaign_logs l
    JOIN cqc_leads c ON l.cqc_location_id = c.cqc_location_id
    WHERE c.campaign_month = target_month AND l.event_type = 'email_opened';

    RETURN json_build_object(
        'leads', leads_count,
        'sent', sent_count,
        'opened', opened_count,
        'replied', replied_count
    );
END;
$$;
"""

sql_analytics = """
CREATE OR REPLACE FUNCTION get_analytics_metrics()
RETURNS json
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    total_leads_count int;
    emailed_leads_count int;
    replied_leads_count int;
    interested_count int;
    booked_count int;
    enriched_count int;
    chart_data json;
    top_subjects json;
BEGIN
    SELECT count(*) INTO total_leads_count FROM cqc_leads;
    SELECT count(*) INTO emailed_leads_count FROM campaign_logs WHERE event_type = 'email_sent' OR event_type LIKE 'sent_email_%';
    SELECT count(*) INTO replied_leads_count FROM cqc_leads WHERE campaign_status NOT IN ('not_started', 'active');
    SELECT count(*) INTO interested_count FROM cqc_leads WHERE campaign_status = 'interested';
    SELECT count(*) INTO booked_count FROM cqc_leads WHERE campaign_status = 'booked';
    SELECT count(*) INTO enriched_count FROM cqc_leads WHERE enrichment_status IN ('enriched', 'done');

    SELECT COALESCE(json_agg(row_to_json(t)), '[]'::json) INTO chart_data
    FROM (
        SELECT 
            'Week ' || row_number() over (order by g.week) as week,
            COALESCE(SUM(CASE WHEN l.event_type = 'email_sent' OR l.event_type LIKE 'sent_email_%' THEN 1 ELSE 0 END), 0) as sent,
            COALESCE(COUNT(DISTINCT CASE WHEN l.event_type = 'email_opened' THEN l.cqc_location_id ELSE NULL END), 0) as opened,
            COALESCE(SUM(CASE WHEN l.event_type = 'email_replied' OR l.event_type LIKE 'reply_received%' THEN 1 ELSE 0 END), 0) as replied
        FROM generate_series(
            date_trunc('week', now() - interval '3 weeks'),
            date_trunc('week', now()),
            interval '1 week'
        ) g(week)
        LEFT JOIN campaign_logs l ON date_trunc('week', l.created_at) = g.week
        GROUP BY g.week
        ORDER BY g.week ASC
    ) t;

    SELECT COALESCE(json_agg(row_to_json(s)), '[]'::json) INTO top_subjects
    FROM (
        SELECT ai_email_subject as subject, count(*) as count
        FROM cqc_leads
        WHERE ai_email_subject IS NOT NULL AND emailed_at IS NOT NULL
        GROUP BY ai_email_subject
        ORDER BY count DESC
        LIMIT 3
    ) s;

    RETURN json_build_object(
        'total_leads', total_leads_count,
        'emailed_leads', emailed_leads_count,
        'replied_leads', replied_leads_count,
        'positive_replied_leads', (interested_count + booked_count),
        'enriched_leads', enriched_count,
        'chart_data', chart_data,
        'top_subjects', top_subjects
    );
END;
$$;
"""

with engine.connect() as conn:
    print("Executing get_global_dashboard_metrics...")
    conn.execute(sqlalchemy.text(sql_dashboard))
    print("Executing get_campaign_month_metrics...")
    conn.execute(sqlalchemy.text(sql_campaigns))
    print("Executing get_analytics_metrics...")
    conn.execute(sqlalchemy.text(sql_analytics))
    print("Running database migrations...")
    conn.execute(sqlalchemy.text("ALTER TABLE campaign_months ADD COLUMN IF NOT EXISTS paused_at timestamp with time zone;"))
    conn.commit()
    print("Successfully created RPC functions.")
