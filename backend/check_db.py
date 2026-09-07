from app.core.database import SessionLocal
from app.models.models import CampaignMonth, CqcLead, CampaignLog
from sqlalchemy import func

def check():
    db = SessionLocal()
    
    print("=" * 60)
    print("CAMPAIGNS:")
    print("=" * 60)
    campaigns = db.query(CampaignMonth).all()
    for c in campaigns:
        print(f"  ID: {c.month_number}, Name: '{c.name}', Status: {c.status}, Limit: {c.daily_limit}, End: {c.end_date}")
        
    print("\n" + "=" * 60)
    print("LEADS PER CAMPAIGN (grouped by status):")
    print("=" * 60)
    counts = db.query(CqcLead.campaign_month, CqcLead.campaign_status, CqcLead.enrichment_status, func.count(CqcLead.id)).group_by(CqcLead.campaign_month, CqcLead.campaign_status, CqcLead.enrichment_status).all()
    for row in counts:
        print(f"  Campaign: {row[0]}, Lead Status: {row[1]}, Enrichment: {row[2]}, Count: {row[3]}")

    print("\n" + "=" * 60)
    print("SAMPLE LEADS (first 4 from each active campaign):")
    print("=" * 60)
    active_campaigns = db.query(CampaignMonth).filter(CampaignMonth.status == 'active').all()
    for c in active_campaigns:
        leads = db.query(CqcLead).filter(CqcLead.campaign_month == c.month_number).limit(4).all()
        print(f"\n  Campaign {c.month_number} ({c.name}):")
        for l in leads:
            print(f"    - {l.contact_first_name} {l.contact_last_name} | {l.contact_email} | status={l.campaign_status} | enrichment={l.enrichment_status} | next_email={l.next_email_date}")

    print("\n" + "=" * 60)
    print("RECENT CAMPAIGN LOGS (last 10):")
    print("=" * 60)
    logs = db.query(CampaignLog).order_by(CampaignLog.created_at.desc()).limit(10).all()
    for log in logs:
        print(f"  {log.created_at} | {log.event_type} | location_id={log.cqc_location_id}")

    db.close()

if __name__ == '__main__':
    check()
