import logging
import threading
import time

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.discussion_routes import router as discussion_router
from app.api.routes import router
from app.config import settings
from app.database import Base, SessionLocal, engine
from app.models import DiscussionItem, ResearchItem
from app.pipeline.discussion_runner import run_discussion_pipeline
from app.pipeline.runner import run_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

for attempt in range(5):
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database connected successfully.")
        break
    except Exception:
        logger.warning("Database connection attempt %d failed, retrying in 3s...", attempt + 1)
        time.sleep(3)
else:
    logger.error("Could not connect to database after 5 attempts.")

app = FastAPI(title="AI Research Agent", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.cors_origins.split(",")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router, prefix="/api")
app.include_router(discussion_router, prefix="/api")


def _scheduled_fetch():
    db = SessionLocal()
    try:
        run_pipeline(db)
    except Exception:
        logger.exception("Scheduled fetch pipeline failed")
    finally:
        db.close()


def _scheduled_discussion_fetch():
    db = SessionLocal()
    try:
        run_discussion_pipeline(db)
    except Exception:
        logger.exception("Scheduled discussion pipeline failed")
    finally:
        db.close()


def _initial_fetch():
    """Run initial pipeline in background so it doesn't block startup."""
    try:
        db = SessionLocal()
        try:
            if db.query(ResearchItem).count() == 0:
                logger.info("Empty database detected - running initial fetch in background.")
                run_pipeline(db)
            else:
                logger.info("Database already has items, skipping initial fetch.")
        finally:
            db.close()
    except Exception:
        logger.exception("Initial fetch failed")


scheduler = BackgroundScheduler()
scheduler.add_job(_scheduled_fetch, "interval", hours=6, id="fetch_pipeline")
scheduler.add_job(_scheduled_discussion_fetch, "interval", hours=6, id="discussion_pipeline")


@app.on_event("startup")
def startup_scheduler():
    scheduler.start()
    # Run initial fetch in a background thread so startup completes fast
    threading.Thread(target=_initial_fetch, daemon=True).start()


@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown(wait=False)
