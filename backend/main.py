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
    # Start APScheduler solely to trigger the MS Graph webhook renewal at startup.
    # NOTE: The outreach pipeline scheduling is handled exclusively by Celery Beat
    # (see app/core/celery.py beat_schedule). Do NOT add pipeline triggers here
    # or tasks will fire twice per interval.
    scheduler = AsyncIOScheduler()

    def trigger_renew_webhooks():
        try:
            celery_app.send_task("app.tasks.email_tasks.renew_webhooks")
            print("Triggered MS Graph webhooks renewal task at startup.")
        except Exception as e:
            print(f"Error triggering webhooks renewal: {e}")

    # Trigger webhook renewal immediately on startup so webhooks are always active
    scheduler.add_job(trigger_renew_webhooks)
    scheduler.start()
    print("Server started. Celery Beat handles pipeline scheduling every 60s.")

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
