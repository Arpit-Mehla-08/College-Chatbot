"""FastAPI application entrypoint."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

# Initialize logging first
from app.core.logging_setup import logger as log
from app.core.config import settings
from app.db.connection import init_mock_db

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize DB and warm up LLM on startup."""
    await init_mock_db()

    # Warm up the LLM provider so the first user query doesn't fail/timeout
    try:
        from app.llm.factory import get_provider
        provider = get_provider()
        await provider.classify_domain("test warmup")
        logging.info("LLM provider warmed up successfully")
    except Exception as e:
        logging.warning(f"LLM warmup failed (non-fatal): {e}")

    yield


app = FastAPI(
    title="College Chatbot API",
    description="Natural Language to SQL chatbot for college data platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler - never expose internal errors to users."""
    return JSONResponse(
        status_code=500,
        content={
            "answer": "Something went wrong on our end. Please try again.",
            "is_clarification": False,
            "conversation_id": "",
            "detail": "Internal server error",
        },
    )


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "llm_provider": settings.LLM_PROVIDER,
        "database": "sqlite" if settings.is_sqlite else "postgresql",
    }


# Import and include routers
from app.api.chat import router as chat_router  # noqa: E402
from app.api.logs import router as logs_router  # noqa: E402
from app.api.conversations import router as conversations_router  # noqa: E402

app.include_router(chat_router, prefix="/api")
app.include_router(logs_router, prefix="/api")
app.include_router(conversations_router, prefix="/api")
