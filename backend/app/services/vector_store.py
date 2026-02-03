"""Vector store service using Qdrant Cloud."""

import uuid
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse

from ..config import get_settings, Settings
from ..models.documents import Chunk, StoredDocument


class VectorStoreService:
    """Service for storing and retrieving document vectors in Qdrant."""

    # Embedding dimension for all-MiniLM-L6-v2
    EMBEDDING_DIMENSION = 384

    def __init__(self, settings: Settings | None = None):
        """Initialize connection to Qdrant Cloud."""
        self.settings = settings or get_settings()
        self.client = QdrantClient(
            url=self.settings.qdrant_url,
            api_key=self.settings.qdrant_api_key,
        )
        self.collection_name = self.settings.qdrant_collection_name
        self._ensure_collection()

    def _ensure_collection(self) -> None:
        """Ensure the collection exists, creating if needed."""
        collection_exists = False
        try:
            self.client.get_collection(self.collection_name)
            collection_exists = True
        except (UnexpectedResponse, Exception):
            # Collection doesn't exist, create it
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=qdrant_models.VectorParams(
                    size=self.EMBEDDING_DIMENSION,
                    distance=qdrant_models.Distance.COSINE,
                ),
            )

        # Always try to create payload indexes (idempotent operation)
        for field_name in ["document_id", "user_id"]:
            try:
                self.client.create_payload_index(
                    collection_name=self.collection_name,
                    field_name=field_name,
                    field_schema=qdrant_models.PayloadSchemaType.KEYWORD,
                )
            except Exception:
                # Index might already exist, which is fine
                pass

    def is_healthy(self) -> bool:
        """Check if Qdrant is accessible."""
        try:
            self.client.get_collection(self.collection_name)
            return True
        except Exception:
            return False

    def add_chunks(
        self,
        chunks: list[Chunk],
        embeddings: list[list[float]],
    ) -> int:
        """
        Add document chunks with their embeddings to the vector store.

        Args:
            chunks: List of document chunks
            embeddings: Corresponding embedding vectors

        Returns:
            Number of chunks added
        """
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have same length")

        if not chunks:
            return 0

        points = [
            qdrant_models.PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "document_title": chunk.document_title,
                    "user_id": chunk.user_id,
                    "page_number": chunk.page_number,
                    "section_title": chunk.section_title,
                    "text": chunk.text,
                    "token_count": chunk.token_count,
                },
            )
            for chunk, embedding in zip(chunks, embeddings)
        ]

        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
        )

        return len(points)

    def search(
        self,
        query_embedding: list[float],
        user_id: str,
        limit: int = 5,
        document_ids: list[str] | None = None,
        min_score: float = 0.5,
    ) -> list[dict[str, Any]]:
        """
        Fast search for similar chunks.

        Args:
            query_embedding: Query vector
            user_id: User ID to filter by (required)
            limit: Maximum results to return
            document_ids: Optional filter to specific documents
            min_score: Minimum relevance score

        Returns:
            List of matching chunks with scores
        """
        # Always filter by user_id
        must_conditions = [
            qdrant_models.FieldCondition(
                key="user_id",
                match=qdrant_models.MatchValue(value=user_id),
            )
        ]

        # Optionally filter by document_ids
        should_conditions = None
        if document_ids:
            should_conditions = [
                qdrant_models.FieldCondition(
                    key="document_id",
                    match=qdrant_models.MatchValue(value=doc_id),
                )
                for doc_id in document_ids
            ]

        query_filter = qdrant_models.Filter(
            must=must_conditions,
            should=should_conditions if should_conditions else None,
        )

        # Single fast query
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=limit * 2,  # Get extra to filter
            query_filter=query_filter,
            with_payload=True,
        )

        # Filter by min_score
        filtered = [
            {
                "score": hit.score,
                **hit.payload,
            }
            for hit in results.points
            if hit.score >= min_score
        ]

        return filtered[:limit]

    def get_document_chunks(self, document_id: str, user_id: str | None = None) -> list[dict[str, Any]]:
        """Get all chunks for a specific document, optionally filtered by user_id."""
        must_conditions = [
            qdrant_models.FieldCondition(
                key="document_id",
                match=qdrant_models.MatchValue(value=document_id),
            )
        ]

        if user_id:
            must_conditions.append(
                qdrant_models.FieldCondition(
                    key="user_id",
                    match=qdrant_models.MatchValue(value=user_id),
                )
            )

        results, _ = self.client.scroll(
            collection_name=self.collection_name,
            scroll_filter=qdrant_models.Filter(must=must_conditions),
            limit=1000,  # Should be enough for a single document
            with_payload=True,
            with_vectors=False,
        )

        return [point.payload for point in results]

    def delete_by_document(self, document_id: str, user_id: str) -> int:
        """
        Delete all chunks for a document belonging to a user.

        Returns:
            Number of chunks deleted
        """
        # Count before deletion (filtered by user_id)
        chunks = self.get_document_chunks(document_id, user_id)
        count = len(chunks)

        if count > 0:
            self.client.delete(
                collection_name=self.collection_name,
                points_selector=qdrant_models.FilterSelector(
                    filter=qdrant_models.Filter(
                        must=[
                            qdrant_models.FieldCondition(
                                key="document_id",
                                match=qdrant_models.MatchValue(value=document_id),
                            ),
                            qdrant_models.FieldCondition(
                                key="user_id",
                                match=qdrant_models.MatchValue(value=user_id),
                            ),
                        ]
                    )
                ),
            )

        return count

    def get_all_documents(self, user_id: str | None = None) -> list[StoredDocument]:
        """Get metadata for all stored documents, optionally filtered by user_id."""
        # Scroll through all points to get unique documents
        documents: dict[str, StoredDocument] = {}

        scroll_filter = None
        if user_id:
            scroll_filter = qdrant_models.Filter(
                must=[
                    qdrant_models.FieldCondition(
                        key="user_id",
                        match=qdrant_models.MatchValue(value=user_id),
                    )
                ]
            )

        offset = None
        while True:
            results, offset = self.client.scroll(
                collection_name=self.collection_name,
                scroll_filter=scroll_filter,
                limit=100,
                offset=offset,
                with_payload=True,
                with_vectors=False,
            )

            if not results:
                break

            for point in results:
                payload = point.payload
                doc_id = payload.get("document_id")

                if doc_id not in documents:
                    documents[doc_id] = StoredDocument(
                        id=doc_id,
                        title=payload.get("document_title", "Unknown"),
                        page_count=0,
                        chunk_count=0,
                        sections=[],
                    )

                doc = documents[doc_id]
                doc.chunk_count += 1
                page_num = payload.get("page_number", 0)
                if page_num > doc.page_count:
                    doc.page_count = page_num

                section = payload.get("section_title")
                if section and section not in doc.sections:
                    doc.sections.append(section)

            if offset is None:
                break

        return list(documents.values())

    def get_document_count(self, user_id: str | None = None) -> int:
        """Get the number of unique documents stored, optionally filtered by user_id."""
        return len(self.get_all_documents(user_id))

    def get_total_chunk_count(self) -> int:
        """Get total number of chunks stored."""
        info = self.client.get_collection(self.collection_name)
        return info.points_count or 0


# Singleton instance
_vector_store: VectorStoreService | None = None


def get_vector_store() -> VectorStoreService:
    """Get or create vector store instance."""
    global _vector_store
    if _vector_store is None:
        _vector_store = VectorStoreService()
    return _vector_store
