"""Internal document models."""

from datetime import datetime
from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """A chunk of text from a document."""

    chunk_id: str = Field(..., description="Unique chunk identifier")
    document_id: str = Field(..., description="Parent document ID")
    document_title: str = Field(..., description="Parent document title")
    page_number: int = Field(..., description="Page number (1-indexed)")
    section_title: str | None = Field(None, description="Section title if detected")
    text: str = Field(..., description="Chunk text content")
    token_count: int = Field(..., description="Approximate token count")


class ProcessedDocument(BaseModel):
    """A processed document with its chunks."""

    id: str = Field(..., description="Document UUID")
    title: str = Field(..., description="Document title")
    page_count: int = Field(..., description="Number of pages")
    chunks: list[Chunk] = Field(default_factory=list)
    sections: list[str] = Field(default_factory=list)
    file_size_bytes: int | None = Field(None, description="Original file size")
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)


class StoredDocument(BaseModel):
    """Document metadata stored in the system."""

    id: str = Field(..., description="Document UUID")
    title: str = Field(..., description="Document title")
    page_count: int = Field(..., description="Number of pages")
    chunk_count: int = Field(..., description="Number of chunks")
    sections: list[str] = Field(default_factory=list)
    file_size_bytes: int | None = Field(None)
    uploaded_at: datetime = Field(default_factory=datetime.utcnow)
