import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.db.base import Base
from app.db.session import engine
from app.db.seed import seed_data

# Section 1 & 2 routers
from app.api.v1.auth import router as auth_router
from app.api.v1.profiles import router as profiles_router
from app.api.v1.careers import router as careers_router
from app.api.v1.skills import router as skills_router
from app.api.v1.roadmaps import router as roadmaps_router
from app.api.v1.assessments import router as assessments_router
from app.api.v1.practice import router as practice_router
from app.api.v1.projects import router as projects_router
from app.api.v1.mentors import router as mentors_router
from app.api.v1.doubts import router as doubts_router
from app.api.v1.admin import router as admin_router
from app.api.v1.analytics import router as analytics_router
from app.api.v1.mentor_chat import router as mentor_chat_router

# Section 3 routers
from app.api.v1.career_intelligence import router as ci_router
from app.api.v1.interviews import router as interviews_router
from app.api.v1.notifications import router as notifications_router
from app.api.v1.reports import router as reports_router
from app.api.v1.portfolio import router as portfolio_router
from app.api.v1.study_plan import router as study_plan_router
from app.api.v1.college import router as college_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("skillpilot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting Skill Pilot AI v3.0...")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    try:
        await seed_data()
    except Exception as e:
        logger.warning(f"Seed note: {e}")
    yield
    logger.info("Skill Pilot AI shutting down.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="3.0.0",
    description="Skill Pilot AI — Career Readiness, Adaptive Learning, Practice Lab, Mentorship, College Connect & Career Intelligence",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_P = settings.API_V1_STR
for r in [
    auth_router, profiles_router, careers_router, skills_router,
    roadmaps_router, assessments_router, practice_router, projects_router,
    mentors_router, doubts_router, admin_router, analytics_router,
    mentor_chat_router,
    # Section 3
    ci_router, interviews_router, notifications_router, reports_router,
    portfolio_router, study_plan_router, college_router,
]:
    app.include_router(r, prefix=_P)


@app.get("/health", tags=["Health"])
@app.get(f"{_P}/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "app": settings.PROJECT_NAME, "version": "3.0.0",
            "environment": settings.ENVIRONMENT}
