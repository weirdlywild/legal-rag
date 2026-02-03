"""Pydantic response models for API endpoints."""

from datetime import datetime
from pydantic import BaseModel, Field


# Health Responses
class HealthResponse(BaseModel):
    """Health check response."""

    status: str = Field(..., description="Service health status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class ComponentStatus(BaseModel):
    """Status of individual system components."""

    vector_store: bool = Field(..., description="Qdrant connection status")
    embedding_model: bool = Field(..., description="Embedding model loaded")
    llm_api: bool = Field(..., description="OpenAI API accessible")


class ReadinessResponse(BaseModel):
    """Readiness check response."""

    ready: bool = Field(..., description="Overall readiness status")
    components: ComponentStatus


# Document Responses
class DocumentSummary(BaseModel):
    """Summary of a document."""

    id: str = Field(..., description="Document UUID")
    title: str = Field(..., description="Document title")
    page_count: int = Field(..., description="Number of pages")
    chunk_count: int = Field(..., description="Number of chunks")
    file_size_bytes: int | None = Field(None, description="File size in bytes")
    uploaded_at: datetime = Field(..., description="Upload timestamp")


class DocumentListResponse(BaseModel):
    """Response for listing documents."""

    documents: list[DocumentSummary] = Field(default_factory=list)
    total: int = Field(..., description="Total number of documents")
    limit_reached: bool = Field(..., description="Whether max documents reached")


class DocumentUploadResponse(BaseModel):
    """Response after uploading a document."""

    id: str = Field(..., description="Document UUID")
    title: str = Field(..., description="Document title")
    page_count: int = Field(..., description="Number of pages")
    chunk_count: int = Field(..., description="Number of chunks created")
    sections_detected: list[str] = Field(default_factory=list)
    processing_time_ms: int = Field(..., description="Processing time in milliseconds")
    message: str = Field(default="Document processed successfully")


class ChunkSummary(BaseModel):
    """Summary of a document chunk."""

    chunk_id: str = Field(..., description="Chunk identifier")
    page_number: int = Field(..., description="Page number")
    section_title: str | None = Field(None, description="Section title")
    token_count: int = Field(..., description="Token count")
    preview: str = Field(..., description="First 100 characters")


class DocumentDetailResponse(BaseModel):
    """Detailed document information."""

    id: str = Field(..., description="Document UUID")
    title: str = Field(..., description="Document title")
    page_count: int = Field(..., description="Number of pages")
    chunks: list[ChunkSummary] = Field(default_factory=list)
    sections: list[str] = Field(default_factory=list)
    uploaded_at: datetime = Field(..., description="Upload timestamp")


class DeleteResponse(BaseModel):
    """Response after deleting a document."""

    success: bool = Field(..., description="Whether deletion succeeded")
    message: str = Field(..., description="Status message")
    chunks_removed: int = Field(default=0, description="Number of chunks removed")


# Query Responses
class Citation(BaseModel):
    """A citation from source documents."""

    document_id: str = Field(..., description="Source document UUID")
    document_title: str = Field(..., description="Source document title")
    page_number: int = Field(..., description="Page number")
    section_title: str | None = Field(None, description="Section title")
    text_snippet: str = Field(..., description="Quoted text passage")
    relevance_score: float = Field(..., ge=0, le=1, description="Relevance score")


class QueryTiming(BaseModel):
    """Timing stats for query processing."""

    embedding_ms: int = Field(..., description="Time to generate query embedding")
    search_ms: int = Field(..., description="Time to search vector store")
    llm_ms: int = Field(..., description="Time for LLM response")
    total_ms: int = Field(..., description="Total processing time")


class QueryUsage(BaseModel):
    """Token usage for a query."""

    retrieval_tokens: int = Field(..., description="Tokens in retrieved chunks")
    llm_input_tokens: int = Field(..., description="Tokens sent to LLM")
    llm_output_tokens: int = Field(..., description="Tokens from LLM response")
    estimated_cost_usd: float = Field(..., description="Estimated cost in USD")
    timing: QueryTiming | None = Field(None, description="Processing time breakdown")


class QueryResponse(BaseModel):
    """Response to a document query."""

    answer: str = Field(..., description="Generated answer")
    citations: list[Citation] = Field(default_factory=list)
    confidence: str = Field(..., description="Confidence level: high, medium, low")
    usage: QueryUsage
    warning: str | None = Field(None, description="Optional warning message")


class InsufficientEvidenceResponse(BaseModel):
    """Response when evidence is insufficient to answer."""

    message: str = Field(..., description="Explanation message")
    reason: str = Field(..., description="Reason code")
    suggestions: list[str] = Field(default_factory=list)
    partial_context: list[Citation] = Field(default_factory=list)


# System Responses
class SystemLimits(BaseModel):
    """System limits configuration."""

    max_documents: int = Field(..., description="Maximum documents allowed")
    max_pages_per_document: int = Field(..., description="Max pages per document")
    max_file_size_mb: int = Field(..., description="Max file size in MB")
    max_question_length: int = Field(..., description="Max question length")
    max_daily_queries: int = Field(..., description="Max queries per day")


class PricingInfo(BaseModel):
    """Pricing information."""

    llm_model: str = Field(..., description="LLM model name")
    input_token_cost_per_1k: float = Field(..., description="Input cost per 1K tokens")
    output_token_cost_per_1k: float = Field(..., description="Output cost per 1K tokens")
    embedding_model: str = Field(..., description="Embedding model info")


class SystemInfoResponse(BaseModel):
    """System information response."""

    limits: SystemLimits
    pricing: PricingInfo
    version: str = Field(..., description="API version")
    environment: str = Field(..., description="Environment name")


class UsageResponse(BaseModel):
    """Current usage statistics."""

    period: str = Field(..., description="Usage period (date)")
    queries_today: int = Field(..., description="Queries made today")
    total_tokens_used: int = Field(default=0, description="Total tokens used")
    total_cost_usd: float = Field(default=0.0, description="Total cost in USD")
    documents_stored: int = Field(default=0, description="Documents currently stored")


# Error Response
class ErrorResponse(BaseModel):
    """Standard error response."""

    error: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: dict | None = Field(None, description="Additional details")
