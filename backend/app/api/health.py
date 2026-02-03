"""Health check endpoints."""

from datetime import datetime

from fastapi import APIRouter

from ..models.responses import HealthResponse, ReadinessResponse, ComponentStatus
from ..services.vector_store import get_vector_store
from ..services.embedding_service import get_embedding_service
from ..services.llm_service import get_llm_service

router = APIRouter(prefix="/health", tags=["health"])


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """
    Basic health check endpoint.

    Returns service status and timestamp.
    Used by load balancers and monitoring systems.
    """
    return HealthResponse(status="healthy", timestamp=datetime.utcnow())


@router.get("/ready", response_model=ReadinessResponse)
async def readiness_check() -> ReadinessResponse:
    """
    Readiness check endpoint.

    Checks all system components and returns their status.
    Use this to verify the service is ready to handle requests.
    """
    # Check each component
    try:
        vector_store = get_vector_store()
        vector_store_ok = vector_store.is_healthy()
    except Exception:
        vector_store_ok = False

    try:
        embedding_service = get_embedding_service()
        embedding_ok = embedding_service.is_healthy()
    except Exception:
        embedding_ok = False

    try:
        llm_service = get_llm_service()
        llm_ok = llm_service.is_healthy()
    except Exception:
        llm_ok = False

    components = ComponentStatus(
        vector_store=vector_store_ok,
        embedding_model=embedding_ok,
        llm_api=llm_ok,
    )

    return ReadinessResponse(
        ready=all([vector_store_ok, embedding_ok, llm_ok]),
        components=components,
    )
