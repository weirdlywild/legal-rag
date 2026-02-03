"""Pydantic request models for API endpoints."""

from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    """Request to query documents."""

    question: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="The question to ask about the documents",
    )
    document_ids: list[str] | None = Field(
        None, description="Optional filter to specific documents"
    )
    max_citations: int = Field(
        default=5, ge=1, le=10, description="Maximum citations to return"
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "question": "What termination clauses apply to this agreement?",
                    "max_citations": 5,
                }
            ]
        }
    }
