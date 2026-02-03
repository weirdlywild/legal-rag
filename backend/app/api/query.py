"""Query/chat endpoint for document Q&A."""

import time
from fastapi import APIRouter, Depends, HTTPException, status

from ..auth import verify_api_key
from ..config import get_settings
from ..models.requests import QueryRequest
from ..models.responses import (
    QueryResponse,
    Citation,
    QueryUsage,
    QueryTiming,
    ErrorResponse,
    InsufficientEvidenceResponse,
)
from ..services.embedding_service import get_embedding_service
from ..services.vector_store import get_vector_store
from ..services.llm_service import get_llm_service
from ..utils.cost_tracker import get_cost_tracker

router = APIRouter(prefix="/query", tags=["query"])


@router.post(
    "",
    response_model=QueryResponse,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        422: {"model": InsufficientEvidenceResponse},
        429: {"model": ErrorResponse},
    },
)
async def query_documents(
    request: QueryRequest,
    _api_key: str = Depends(verify_api_key),
) -> QueryResponse:
    """
    Ask a question about uploaded documents.

    Returns an answer grounded in the source documents with citations.
    If insufficient evidence is found, returns a 422 status with partial context.
    """
    settings = get_settings()
    cost_tracker = get_cost_tracker()

    # Check usage limits
    can_proceed, limit_message = cost_tracker.can_process_query()
    if not can_proceed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=limit_message,
        )

    embedding_service = get_embedding_service()
    vector_store = get_vector_store()
    llm_service = get_llm_service()

    # Start total timing
    total_start = time.time()

    # Check if any documents are uploaded
    doc_count = vector_store.get_document_count()
    if doc_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No documents uploaded. Please upload a PDF document first.",
        )

    # Generate query embedding (with timing)
    embed_start = time.time()
    query_embedding = embedding_service.embed_text(request.question)
    embed_time_ms = int((time.time() - embed_start) * 1000)

    # Retrieve relevant chunks (with timing)
    search_start = time.time()
    chunks = vector_store.search(
        query_embedding=query_embedding,
        limit=request.max_citations or settings.top_k_chunks,
        document_ids=request.document_ids,
        min_score=settings.min_relevance_score,
    )
    search_time_ms = int((time.time() - search_start) * 1000)

    # Build citations from retrieved chunks
    citations = [
        Citation(
            document_id=chunk.get("document_id", ""),
            document_title=chunk.get("document_title", "Unknown"),
            page_number=chunk.get("page_number", 0),
            section_title=chunk.get("section_title"),
            text_snippet=chunk.get("text", "")[:500],  # Truncate for response
            relevance_score=chunk.get("score", 0.0),
        )
        for chunk in chunks
    ]

    # Check if we have any relevant chunks
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Unable to answer this question based on available documents.",
                "reason": "no_relevant_chunks",
                "suggestions": [
                    "Try rephrasing your question",
                    "Ensure the documents contain information about this topic",
                    "Ask about topics covered in the uploaded documents",
                ],
                "partial_context": [],
            },
        )

    # Generate answer with GPT-4o (with timing)
    llm_start = time.time()
    result = llm_service.generate_answer(
        question=request.question,
        context_chunks=chunks,
    )
    llm_time_ms = int((time.time() - llm_start) * 1000)
    total_time_ms = int((time.time() - total_start) * 1000)

    # Track usage
    cost_tracker.track_query(
        input_tokens=result["input_tokens"],
        output_tokens=result["output_tokens"],
        cost_usd=result["cost_usd"],
    )

    # Check for low confidence / insufficient evidence
    answer_lower = result["answer"].lower()
    if (
        result["confidence"] == "low" and
        ("cannot find sufficient" in answer_lower or "insufficient information" in answer_lower)
    ):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "message": "Unable to answer this question based on available documents.",
                "reason": "low_confidence",
                "suggestions": [
                    "The documents may not contain information about this specific topic",
                    "Try asking a more specific question",
                    "Check if the relevant document is uploaded",
                ],
                "partial_context": [c.model_dump() for c in citations],
            },
        )

    # Calculate retrieval tokens
    retrieval_tokens = sum(chunk.get("token_count", 0) for chunk in chunks)

    # Build warning if confidence is low
    warning = None
    if result["confidence"] == "low":
        warning = "The answer has low confidence. Please verify with the source documents."
    elif result["confidence"] == "medium":
        warning = "Some parts of this answer may require additional verification."

    return QueryResponse(
        answer=result["answer"],
        citations=citations,
        confidence=result["confidence"],
        usage=QueryUsage(
            retrieval_tokens=retrieval_tokens,
            llm_input_tokens=result["input_tokens"],
            llm_output_tokens=result["output_tokens"],
            estimated_cost_usd=result["cost_usd"],
            timing=QueryTiming(
                embedding_ms=embed_time_ms,
                search_ms=search_time_ms,
                llm_ms=llm_time_ms,
                total_ms=total_time_ms,
            ),
        ),
        warning=warning,
    )
