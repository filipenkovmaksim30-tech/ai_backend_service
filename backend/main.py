from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api import contact_router, health_router, metrics_router
from backend.core.error_handlers import register_exception_handlers
from backend.core.logging_config import setup_logging
from backend.core.middleware import request_logging_middleware
from backend.core.settings import get_settings
from backend.db.session import async_engine

settings = get_settings()
setup_logging(settings)


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await async_engine.dispose()


app = FastAPI(
    title="AI Backend Contact Service Тестовое задание",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Accept", "Content-Type"],
)
app.middleware("http")(request_logging_middleware)
register_exception_handlers(app)
app.include_router(contact_router)
app.include_router(health_router)
app.include_router(metrics_router)
