"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # API Settings
    app_name: str = "Legal AI RAG API"
    app_version: str = "1.0.0"
    environment: str = "development"
    api_prefix: str = "/api/v1"

    # Authentication
    api_key: str  # Required - set via environment variable
    app_password: str  # Required - password for frontend access

    # OpenAI Configuration
    openai_api_key: str  # Required - set via environment variable
    openai_model: str = "gpt-4o-mini"  # Faster than gpt-4o, still high quality
    openai_max_tokens: int = 1000  # Reduced for faster responses
    openai_temperature: float = 0.1

    # Qdrant Cloud Configuration
    qdrant_url: str  # Required - set via environment variable
    qdrant_api_key: str  # Required - set via environment variable
    qdrant_collection_name: str = "legal_documents"

    # Document Limits
    max_documents: int = 10
    max_pages_per_document: int = 80
    max_file_size_mb: int = 10

    # Chunking Configuration
    chunk_size_tokens: int = 600
    chunk_overlap_tokens: int = 100

    # Retrieval Configuration
    top_k_chunks: int = 6  # Balanced for speed and context
    min_relevance_score: float = 0.10  # Slightly higher to reduce noise

    # Cost Control
    max_daily_queries: int = 100
    max_daily_cost_usd: float = 1.00

    # OpenAI Pricing (per 1K tokens) - GPT-4o-mini pricing
    gpt4o_input_cost_per_1k: float = 0.00015
    gpt4o_output_cost_per_1k: float = 0.0006

    # CORS Configuration - accepts JSON string or list
    cors_origins: list[str] = ["http://localhost:3000", "https://legal.rajsinh.work"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
