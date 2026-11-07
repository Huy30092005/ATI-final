"""
ARA Backend Configuration
Loads environment variables and application settings.
"""

from typing import List, Optional
from pydantic_settings import BaseSettings, SettingsConfigDict
import os
from dotenv import load_dotenv

load_dotenv()


class Settings(BaseSettings):
    # Application
    APP_NAME: str = "ARA - AI Research Assistant"
    API_V1_STR: str = "/api"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    PORT: int = 8000
    HOST: str = "0.0.0.0"

    # CORS
    # Override with a JSON list in .env, e.g. CORS_ORIGINS=["https://app.example.com"]
    CORS_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]

    # Uploads
    MAX_UPLOAD_MB: int = 10

    # OpenAI Settings
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY")  
    OPENAI_MODEL: str = "gpt-4o-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    # MongoDB Atlas Vector Search
    MONGODB_URI: str = os.getenv("MONGODB_URI")
    MONGODB_DB_NAME: str = "ara_research_db"
    MONGODB_COLLECTION: str = "document_embeddings"
    MONGODB_INDEX_NAME: str = "vector_index"

    # Search Services
    TAVILY_API_KEY: Optional[str] = None
    SERPAPI_API_KEY: Optional[str] = None
    SEARCH_PROVIDER: str = "duckduckgo"  # duckduckgo, tavily, or serpapi

    # Quality Control & Scoring Thresholds
    DEFAULT_MIN_CREDIBILITY: float = 0.60
    MAX_EVIDENCE_PER_QUERY: int = 15
    CHUNK_SIZE: int = 800
    CHUNK_OVERLAP: int = 150

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
