from sqlalchemy import Column, Integer, String, Text, Enum, DateTime, Date, JSON, func, ForeignKey
from sqlalchemy.orm import declarative_base
import enum
from app.core.database import Base

class CqcLead(Base):
    __tablename__ = "cqc_leads"

    id = Column(Integer, primary_key=True, index=True)
    cqc_location_id = Column(String(50), unique=True, index=True)
    company_name = Column(String(255))
    contact_first_name = Column(String(100))
    contact_last_name = Column(String(100))
    contact_email = Column(String(255))
    phone = Column(String(50))
    website_url = Column(String(255))
    service_type = Column(Text)
    specialisms = Column(Text)
    provider_name = Column(String(255))
    local_authority = Column(String(100))
    region = Column(String(100))
    
    enrichment_status = Column(String(50))
    campaign_status = Column(String(50), default='not_started')
    campaign_month = Column(Integer, nullable=True) # Month 1, Month 2, Month 3, etc.
    
    scraped_content = Column(Text)
    ai_email_subject = Column(Text)
    ai_email_body = Column(Text)
    full_email_sequence = Column(JSON)
    sequence_step = Column(Integer, default=0)
    next_email_date = Column(DateTime(timezone=True))
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    enriched_at = Column(DateTime(timezone=True))
    emailed_at = Column(DateTime(timezone=True))

class CampaignLog(Base):
    __tablename__ = "campaign_logs"

    id = Column(Integer, primary_key=True, index=True)
    cqc_location_id = Column(String(50))
    event_type = Column(String(50))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    cqc_location_id = Column(String(50), index=True, nullable=True)
    attendee_name = Column(String(255))
    attendee_email = Column(String(255))
    start_time = Column(DateTime(timezone=True))
    end_time = Column(DateTime(timezone=True))
    status = Column(String(50), default="ACCEPTED")
    meeting_url = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class CampaignMonth(Base):
    __tablename__ = "campaign_months"

    month_number = Column(Integer, primary_key=True)
    status = Column(String(50), default="queued") # 'active', 'queued', 'completed'
    start_date = Column(DateTime(timezone=True))
    end_date = Column(DateTime(timezone=True))
    paused_at = Column(DateTime(timezone=True), nullable=True)
    leads_count = Column(Integer, default=1000)

class OutlookMessage(Base):
    __tablename__ = "outlook_messages"

    id = Column(Integer, primary_key=True, index=True)
    message_id = Column(String(255), unique=True, index=True)
    conversation_id = Column(String(255), index=True)
    lead_id = Column(Integer, ForeignKey("cqc_leads.id", ondelete="CASCADE"), nullable=False)
    folder = Column(String(50)) # 'inbox' or 'sentitems'
    sender_email = Column(String(255))
    recipient_email = Column(String(255))
    subject = Column(Text)
    body = Column(Text)
    received_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class SyncToken(Base):
    __tablename__ = "sync_tokens"

    id = Column(Integer, primary_key=True, index=True)
    folder = Column(String(50), unique=True, index=True) # 'inbox' or 'sentitems'
    delta_token = Column(Text, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now(), server_default=func.now())

