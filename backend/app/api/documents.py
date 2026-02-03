"""Document management endpoints."""

import time
from datetime import datetime

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from ..auth import verify_api_key
from ..config import get_settings
from ..models.responses import (
    DocumentListResponse,
    DocumentSummary,
    DocumentUploadResponse,
    DocumentDetailResponse,
    ChunkSummary,
    DeleteResponse,
    ErrorResponse,
)
from ..services.pdf_processor import get_pdf_processor
from ..services.embedding_service import get_embedding_service
from ..services.vector_store import get_vector_store

router = APIRouter(prefix="/documents", tags=["documents"])


@router.get(
    "",
    response_model=DocumentListResponse,
    responses={401: {"model": ErrorResponse}, 403: {"model": ErrorResponse}},
)
async def list_documents(
    _api_key: str = Depends(verify_api_key),
) -> DocumentListResponse:
    """
    List all uploaded documents.

    Returns document metadata including page count, chunk count, and upload date.
    """
    settings = get_settings()
    vector_store = get_vector_store()

    stored_docs = vector_store.get_all_documents()

    documents = [
        DocumentSummary(
            id=doc.id,
            title=doc.title,
            page_count=doc.page_count,
            chunk_count=doc.chunk_count,
            file_size_bytes=doc.file_size_bytes,
            uploaded_at=doc.uploaded_at,
        )
        for doc in stored_docs
    ]

    return DocumentListResponse(
        documents=documents,
        total=len(documents),
        limit_reached=len(documents) >= settings.max_documents,
    )


@router.post(
    "",
    response_model=DocumentUploadResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def upload_document(
    file: UploadFile = File(..., description="PDF file to upload"),
    title: str | None = Form(None, description="Optional custom title"),
    _api_key: str = Depends(verify_api_key),
) -> DocumentUploadResponse:
    """
    Upload a PDF document for processing.

    The document will be parsed, chunked, and indexed for retrieval.
    Maximum 2 documents, 80 pages per document, 10MB file size.
    """
    settings = get_settings()
    pdf_processor = get_pdf_processor()
    embedding_service = get_embedding_service()
    vector_store = get_vector_store()

    # Check document limit
    current_count = vector_store.get_document_count()
    if current_count >= settings.max_documents:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Document limit reached ({settings.max_documents}). Delete a document first.",
        )

    # Read file content
    content = await file.read()
    filename = file.filename or "document.pdf"

    # Validate file
    is_valid, error_msg = pdf_processor.validate_file(content, filename)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_msg,
        )

    # Process PDF
    start_time = time.time()
    try:
        processed_doc = pdf_processor.process_pdf(content, filename, title)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to process PDF: {str(e)}",
        )

    # Generate embeddings for chunks
    chunk_texts = [chunk.text for chunk in processed_doc.chunks]
    embeddings = embedding_service.embed_texts(chunk_texts)

    # Store in vector database
    vector_store.add_chunks(processed_doc.chunks, embeddings)

    processing_time_ms = int((time.time() - start_time) * 1000)

    return DocumentUploadResponse(
        id=processed_doc.id,
        title=processed_doc.title,
        page_count=processed_doc.page_count,
        chunk_count=len(processed_doc.chunks),
        sections_detected=processed_doc.sections,
        processing_time_ms=processing_time_ms,
        message=f"Document processed successfully. Created {len(processed_doc.chunks)} searchable chunks.",
    )


@router.get(
    "/{document_id}",
    response_model=DocumentDetailResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def get_document(
    document_id: str,
    _api_key: str = Depends(verify_api_key),
) -> DocumentDetailResponse:
    """
    Get detailed information about a document.

    Returns document metadata and a list of all chunks with previews.
    """
    vector_store = get_vector_store()

    # Get chunks for this document
    chunks_data = vector_store.get_document_chunks(document_id)

    if not chunks_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    # Build response
    chunks = [
        ChunkSummary(
            chunk_id=c.get("chunk_id", ""),
            page_number=c.get("page_number", 0),
            section_title=c.get("section_title"),
            token_count=c.get("token_count", 0),
            preview=c.get("text", "")[:100] + "..." if len(c.get("text", "")) > 100 else c.get("text", ""),
        )
        for c in chunks_data
    ]

    # Extract document info from first chunk
    first_chunk = chunks_data[0]
    title = first_chunk.get("document_title", "Unknown")

    # Calculate page count from max page number
    page_count = max(c.get("page_number", 0) for c in chunks_data)

    # Extract unique sections
    sections = list(set(
        c.get("section_title")
        for c in chunks_data
        if c.get("section_title")
    ))

    return DocumentDetailResponse(
        id=document_id,
        title=title,
        page_count=page_count,
        chunks=chunks,
        sections=sections,
        uploaded_at=datetime.utcnow(),  # TODO: Store actual upload time
    )


@router.delete(
    "/{document_id}",
    response_model=DeleteResponse,
    responses={
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
    },
)
async def delete_document(
    document_id: str,
    _api_key: str = Depends(verify_api_key),
) -> DeleteResponse:
    """
    Delete a document and all its chunks.

    This action cannot be undone.
    """
    vector_store = get_vector_store()

    # Check if document exists
    chunks = vector_store.get_document_chunks(document_id)
    if not chunks:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document not found: {document_id}",
        )

    # Delete the document
    chunks_removed = vector_store.delete_by_document(document_id)

    return DeleteResponse(
        success=True,
        message=f"Document deleted successfully.",
        chunks_removed=chunks_removed,
    )
