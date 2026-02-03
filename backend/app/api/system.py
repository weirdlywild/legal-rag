"""System information endpoints."""

from datetime import date

from fastapi import APIRouter

from ..config import get_settings
from ..models.responses import (
    SystemInfoResponse,
    SystemLimits,
    PricingInfo,
    UsageResponse,
)
from ..services.vector_store import get_vector_store
from ..utils.cost_tracker import get_cost_tracker

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info", response_model=SystemInfoResponse)
async def get_system_info() -> SystemInfoResponse:
    """
    Get system information and limits.

    Returns configuration limits, pricing info, and version.
    Use this to understand system constraints before uploading documents.
    """
    settings = get_settings()

    limits = SystemLimits(
        max_documents=settings.max_documents,
        max_pages_per_document=settings.max_pages_per_document,
        max_file_size_mb=settings.max_file_size_mb,
        max_question_length=500,
        max_daily_queries=settings.max_daily_queries,
    )

    pricing = PricingInfo(
        llm_model=settings.openai_model,
        input_token_cost_per_1k=settings.gpt4o_input_cost_per_1k,
        output_token_cost_per_1k=settings.gpt4o_output_cost_per_1k,
        embedding_model="all-MiniLM-L6-v2 (local, free)",
    )

    return SystemInfoResponse(
        limits=limits,
        pricing=pricing,
        version=settings.app_version,
        environment=settings.environment,
    )


@router.get("/usage", response_model=UsageResponse)
async def get_usage_stats() -> UsageResponse:
    """
    Get current usage statistics.

    Returns queries made today, tokens used, and estimated cost.
    """
    cost_tracker = get_cost_tracker()
    vector_store = get_vector_store()

    stats = cost_tracker.get_usage_stats()

    return UsageResponse(
        period=stats["period"],
        queries_today=stats["queries_today"],
        total_tokens_used=stats["total_tokens_used"],
        total_cost_usd=stats["total_cost_usd"],
        documents_stored=vector_store.get_document_count(),
    )
