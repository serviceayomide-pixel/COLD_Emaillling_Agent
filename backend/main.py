from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
import asyncio
from contextlib import asynccontextmanager
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from zoneinfo import ZoneInfo
from app.api.webhooks_smtp_ghost import router as webhook_router
from app.api.webhooks_cal import router as cal_webhook_router
from app.api.webhooks_graph import router as graph_webhook_router
from app.api.routes_dashboard import router as dashboard_router
from app.api.routes_ingestion import router as ingestion_router
from app.api.routes_tracking import router as tracking_router
from app.core.celery import celery_app

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Use APScheduler to run background tasks natively inside the FastAPI container.
    # This eliminates the need for separate Celery Worker/Beat services on Railway.
    scheduler = AsyncIOScheduler()

    from scripts.manage_graph_webhooks import manage_webhooks
    from app.worker import run_pipeline

    def run_webhooks_sync():
        print("Running scheduled MS Graph webhooks renewal...")
        asyncio.create_task(manage_webhooks())

    def run_outreach_sync():
        # print("Triggering 60s outreach pipeline...")
        asyncio.create_task(run_pipeline())

    # Trigger webhook renewal immediately on startup, then every 12 hours
    scheduler.add_job(run_webhooks_sync)
    scheduler.add_job(run_webhooks_sync, 'interval', hours=12)
    
    # Trigger the outreach worker every 60 seconds
    scheduler.add_job(run_outreach_sync, 'interval', seconds=60)
    
    scheduler.start()
    print("Server started. APScheduler is natively handling background tasks.")

    yield
    scheduler.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version="1.4.0",
    description="Autonomous Client Acquisition AI Engine",
    lifespan=lifespan
)

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

app.include_router(webhook_router, prefix="/api", tags=["webhooks"])
app.include_router(cal_webhook_router, prefix="/api", tags=["webhooks"])
app.include_router(graph_webhook_router, prefix="/api", tags=["webhooks"])
app.include_router(dashboard_router, prefix="/api", tags=["dashboard"])
app.include_router(ingestion_router, prefix="/api", tags=["ingestion"])
app.include_router(tracking_router, prefix="/api", tags=["tracking"])

@app.get("/api/check_redis")
def check_redis():
    import redis
    try:
        r = redis.Redis.from_url(settings.REDIS_URL)
        return {
            "status": "success",
            "redis_url": settings.REDIS_URL,
            "ping": r.ping(),
            "keys": [str(k) for k in r.keys("*")]
        }
    except Exception as e:
        return {
            "status": "error",
            "redis_url": settings.REDIS_URL,
            "message": str(e)
        }

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.get("/")
def read_root():
    return {"message": "Client Acquisition AI Engine is running", "version": "1.4.0"}
