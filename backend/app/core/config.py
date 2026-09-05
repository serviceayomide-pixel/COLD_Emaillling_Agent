from pydantic_settings import BaseSettings
from typing import List, Optional

class Settings(BaseSettings):
    PROJECT_NAME: str = "Client Acquisition AI Engine"
    BACKEND_CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "https://frontend-production-cc0b.up.railway.app",
    ]
    
    # Sender Information
    SENDER_NAME: str = "Gabriel Taylor"
    COMPANY_NAME: str = "GEN128 Solution"

    # Database (Supabase)
    DATABASE_URL: str = ""
    SUPABASE_URL: str = ""
    SUPABASE_ANON_KEY: str = ""
    SUPABASE_SERVICE_ROLE_KEY: str = ""

    # API Keys - filled from .env file
    OPENROUTER_API_KEY: str = ""
    WIZLEAD_API_KEY: str = ""
    FIRECRAWL_API_KEY: str = ""
    SERPER_API_KEY: str = ""

    # SMTP Ghost / Generic SMTP Relay (No longer needed, using Graph API)
    # Kept empty strings for backward compatibility if needed, but not used.
    # Cal.com
    CAL_API_KEY: str = ""
    CAL_BOOKING_URL: str = "https://cal.com/gabriel-taylor-mfgspz/15min"  # Override in testing env to /30min
    # Microsoft Inbox integration
    MICROSOFT_EMAIL: Optional[str] = None
    MICROSOFT_TENANT_ID: Optional[str] = None
    MICROSOFT_CLIENT_ID: Optional[str] = None
    MICROSOFT_CLIENT_SECRET: Optional[str] = None

    # Redis & Background Tasks
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # Webhook Secrets
    WEBHOOK_SECRET: str = "super_secret_webhook_key_123"

    # Tracking
    TRACKING_BASE_URL: str = ""  # e.g. https://your-app.railway.app

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

settings = Settings()
