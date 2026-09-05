import asyncio
from datetime import datetime, timezone, timedelta
from app.core.database import SessionLocal
from app.models.models import CqcLead, CampaignLog, CampaignMonth
from app.services import firecrawl, openrouter, email_sender
from sqlalchemy import or_, and_

async def process_lead(db, lead: CqcLead) -> bool:
    """Processes a single lead for the current step in their sequence."""
    print(f"Processing Lead: {lead.contact_first_name} {lead.contact_last_name} at {lead.company_name} (Step: {lead.sequence_step})")
    
    # Generate Sequence if this is the first time
    if lead.sequence_step == 0 or not lead.full_email_sequence:
        context = lead.scraped_content
        if not context:
            print(f"No scraped context found for {lead.company_name}. Scraping via Firecrawl...")
            domain = lead.website_url or f"{lead.company_name.replace(' ', '')}.com"
            context = await firecrawl.scrape_company_context(f"https://{domain}")
            if context:
                lead.scraped_content = context
            else:
                context = f"{lead.company_name} is a healthcare provider in the UK." # Fallback
                
        print(f"Generating personalized email sequence for {lead.contact_first_name}...")
        email_sequence = await openrouter.generate_email_sequence(lead.contact_first_name, lead.company_name, context)
        
        if not email_sequence:
            print(f"Failed to generate sequence for {lead.contact_email}")
            return False
            
        lead.full_email_sequence = email_sequence
        db.commit()

    # Determine which email to send
    sequence = lead.full_email_sequence
    step_key = f"email_{lead.sequence_step + 1}"
    
    if step_key not in sequence:
        print(f"No email found for step {step_key} for {lead.contact_email}")
        return False
        
    email_to_send = sequence[step_key]
    
    print(f"Sending {step_key} to {lead.contact_email} via Outlook Graph...")
    success = await email_sender.send_email(
        to_email=lead.contact_email,
        subject=email_to_send.get("subject", "Following up"),
        body=email_to_send.get("body", ""),
        lead_id=lead.id
    )
    
    if success:
        # Update sequence tracking
        lead.sequence_step += 1
        lead.emailed_at = datetime.now(timezone.utc)
        lead.campaign_status = 'active'
        lead.ai_email_subject = email_to_send.get("subject", "Following up")
        lead.ai_email_body = email_to_send.get("body", "")
        
        # Log event
        log = CampaignLog(cqc_location_id=lead.cqc_location_id, event_type=f"sent_{step_key}")
        db.add(log)
        
        # Schedule next email
        now_date = datetime.now(timezone.utc)
        if lead.sequence_step == 1:
            lead.next_email_date = now_date + timedelta(days=3) # Follow up after 3 days
        elif lead.sequence_step == 2:
            lead.next_email_date = now_date + timedelta(days=4) # Follow up after 7 days total (3 + 4 = 7)
        elif lead.sequence_step == 3:
            lead.next_email_date = now_date + timedelta(days=7) # Follow up after 14 days total (7 + 7 = 14)
        else:
            # Reached the end of the sequence
            lead.next_email_date = None
            lead.campaign_status = 'finished'
            
        db.commit()
        print(f"Successfully sent {step_key} and scheduled next step for {lead.contact_email}")
        return True
    else:
        print(f"Failed to send email to {lead.contact_email}. Pushing next attempt out by 1 hour to prevent worker jams.")
        # Graceful retry: ensure it's "active" so it requires a time check, then add 1 hour
        if lead.campaign_status == 'not_started':
            lead.campaign_status = 'active'
        lead.next_email_date = datetime.now(timezone.utc) + timedelta(hours=1)
        db.commit()
        return False


async def run_pipeline():
    """Main worker entry point. Runs every minute in test mode."""
    print("Outreach worker pipeline starting check...")
        
    db = SessionLocal()
    try:
        now_date = datetime.now(timezone.utc)
        
        # 1. Transition active month if end date has passed
        ended_month = db.query(CampaignMonth).filter(
            CampaignMonth.status == 'active',
            CampaignMonth.end_date <= now_date
        ).first()
        
        if ended_month:
            print(f"Campaign Month {ended_month.month_number} has ended.")
            ended_month.status = "completed"
            
            # Activate next queued month
            next_month = db.query(CampaignMonth).filter(
                CampaignMonth.status == "queued",
                CampaignMonth.month_number == ended_month.month_number + 1
            ).first()
            if next_month:
                next_month.status = "active"
                print(f"Campaign Month {next_month.month_number} is now active.")
            db.commit()
            
        # 2. Get the active campaign month
        active_month = db.query(CampaignMonth).filter(CampaignMonth.status == 'active').first()
        if not active_month:
            # If any month is explicitly paused, respect it and skip sending
            paused_month = db.query(CampaignMonth).filter(CampaignMonth.status == 'paused').first()
            if paused_month:
                print(f"Campaign Month {paused_month.month_number} is PAUSED. Skipping outreach.")
                return
                
            # Fallback/initialize Month 1 to active if it is still queued/not started
            month1 = db.query(CampaignMonth).filter(CampaignMonth.month_number == 1).first()
            if month1 and month1.status in ('queued', 'not_started'):
                month1.status = 'active'
                db.commit()
                active_month = month1
            else:
                print("No active or paused campaign month found. Skipping outreach.")
                return
                
        active_month_number = active_month.month_number
        print(f"Active Campaign Month: Month {active_month_number}")
        
        # 3. Find leads belonging to the active month that are due for an email
        pending_leads = db.query(CqcLead).filter(
            CqcLead.enrichment_status == 'enriched',
            CqcLead.campaign_month == active_month_number,
            or_(
                CqcLead.campaign_status == 'not_started',
                and_(
                    or_(
                        CqcLead.campaign_status == 'active',
                        CqcLead.campaign_status == 'out of office'
                    ),
                    CqcLead.next_email_date <= now_date
                )
            )
        ).with_for_update(skip_locked=True).limit(1).all() # Limit to exactly 1 lead per run to space out sending
        
        if pending_leads:
            print(f"Found lead due for email in Month {active_month_number}. Starting dispatch...")
            for lead in pending_leads:
                await process_lead(db, lead)
        else:
            print(f"No pending leads due for emails in Month {active_month_number} right now.")
            
        # 4. Auto-queue next month in advance
        if active_month:
            next_month_number = active_month_number + 1
            next_month_exists = db.query(CampaignMonth).filter(CampaignMonth.month_number == next_month_number).first()
            
            if not next_month_exists:
                print(f"Active Month {active_month_number} is active. Queuing Month {next_month_number} in advance...")
                
                # Queue next month
                start_date = active_month.end_date
                end_date = start_date + timedelta(days=30)
                
                # Pull next 1000 leads that are enriched (verified)
                next_leads = db.query(CqcLead).filter(
                    CqcLead.campaign_month.is_(None),
                    CqcLead.enrichment_status == 'enriched'
                ).order_by(CqcLead.id).limit(1000).all()
                
                if next_leads:
                    for l in next_leads:
                        l.campaign_month = next_month_number
                        
                    new_month = CampaignMonth(
                        month_number=next_month_number,
                        status="queued",
                        start_date=start_date,
                        end_date=end_date,
                        leads_count=len(next_leads)
                    )
                    db.add(new_month)
                    db.commit()
                    print(f"Successfully queued Month {next_month_number} with {len(next_leads)} leads.")
                else:
                    print("No remaining leads in DB to queue for the next month.")
                        
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_pipeline())

