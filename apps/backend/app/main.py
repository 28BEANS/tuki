"""
Tuki Backend — FastAPI Application

Hyperlocal commuting backend for Angeles City, Pampanga.
"""

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.db.session import close_db, init_db
from app.middleware.error_handler import ErrorHandlerMiddleware
from app.middleware.logging import LoggingMiddleware
from app.services.graph_service import graph_service

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
)
# Third-party HTTP INFO logs include full legacy Google Places query strings,
# including API credentials. Keep provider traffic out of application logs.
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logger = logging.getLogger("tuki")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown hooks."""
    settings = get_settings()

    logger.info("Starting Tuki API (%s)", settings.app_env)

    # Startup
    try:
        await init_db()
        logger.info("Database connection pool initialized")
    except Exception as e:
        logger.warning("Database connection failed (will retry on first request): %s", e)

    # Build transport graph once and cache in memory
    await graph_service.initialise()

    yield

    # Shutdown
    await close_db()
    logger.info("Database connection pool closed")


def create_app() -> FastAPI:
    """Application factory."""
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description=(
            "Tuki — Hyperlocal commuting API for Angeles City, Pampanga. "
            "Provides multimodal route planning, fare estimation, "
            "landmark-based navigation, and ride-hailing comparison."
        ),
        docs_url="/docs" if settings.is_development else None,
        redoc_url="/redoc" if settings.is_development else None,
        lifespan=lifespan,
    )

    # --- Middleware (order matters: last added = first executed) ---
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"] if settings.is_development else [],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(ErrorHandlerMiddleware)
    app.add_middleware(LoggingMiddleware)

    # --- Routes ---
    app.include_router(api_router)

    return app


# App instance for uvicorn
app = create_app()
