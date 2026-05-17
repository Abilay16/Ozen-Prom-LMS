from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import engine, Base
from app.api.v1.router import api_router


async def _seed_training_types(session: AsyncSession) -> None:
    """Seed reference training types if the table is empty."""
    from app.models.training_type import TrainingType
    count_result = await session.execute(select(func.count()).select_from(TrainingType))
    if count_result.scalar() == 0:
        session.add_all([
            TrainingType(code="biot",    name_ru="Безопасность и охрана труда",    name_short="БиОТ",    validity_years=1),
            TrainingType(code="ptm",     name_ru="Пожарно-технический минимум",     name_short="ПТМ",     validity_years=3),
            TrainingType(code="prombez", name_ru="Промышленная безопасность",        name_short="ПромБез", validity_years=1),
            TrainingType(code="elektro", name_ru="Электробезопасность",             name_short="ЭлБез",   validity_years=1),
        ])
        await session.commit()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    async with AsyncSession(engine) as session:
        await _seed_training_types(session)
    yield
    # Shutdown
    await engine.dispose()


app = FastAPI(
    title="Ozen-Prom LMS API",
    description="LMS platform for occupational safety training",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routes
app.include_router(api_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {"status": "ok", "version": "1.0.0"}
