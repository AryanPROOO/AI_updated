import logging

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

Base.metadata.create_all(bind=engine)

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
    finally:
        db.close()


def _scheduled_discussion_fetch():
    db = SessionLocal()
    try:
        run_discussion_pipeline(db)
    finally:
        db.close()


scheduler = BackgroundScheduler()
# Run every 6 hours to fetch fresh data
scheduler.add_job(_scheduled_fetch, "interval", hours=6, id="fetch_pipeline")
scheduler.add_job(_scheduled_discussion_fetch, "interval", hours=6, id="discussion_pipeline")
scheduler.start()

@app.on_event("startup")
def startup_pipeline():
    db = SessionLocal()
    try:
        if db.query(ResearchItem).count() == 0:
            logger.info("Empty database detected - running initial fetch.")
            run_pipeline(db)
    finally:
        db.close()


@app.on_event("shutdown")
def shutdown_scheduler():
    scheduler.shutdown(wait=False)
