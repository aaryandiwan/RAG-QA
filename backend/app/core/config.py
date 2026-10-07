from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import field_validator
from typing import List, Optional

BACKEND_DIR = Path(__file__).resolve().parent.parent.parent
ENV_PATH = BACKEND_DIR / ".env"


class Settings(BaseSettings):
    # Gemini
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "models/gemini-3.5-flash-lite"
    GEMINI_EMBEDDING_MODEL: str = "models/gemini-embedding-001"

    # Pinecone
    PINECONE_API_KEY: str = ""
    PINECONE_ENV: str = "us-east-1"
    PINECONE_INDEX: str = "rag-qa-index"

    # Chunking
    CHUNK_SIZE: int = 500
    CHUNK_OVERLAP: int = 50
    TOP_K_RESULTS: int = 5

    # Embedding dimension (gemini-embedding-001 = 3072)
    EMBEDDING_DIMENSION: int = 3072

    # File upload
    MAX_FILE_SIZE_MB: int = 20
    ALLOWED_EXTENSIONS: List[str] = ["pdf", "docx", "txt", "md"]

    # CORS
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]

    @field_validator("GEMINI_API_KEY", "PINECONE_API_KEY", mode="before")
    @classmethod
    def clean_api_keys(cls, v):
        if isinstance(v, str):
            return v.strip()
        return v

    class Config:
        env_file = str(ENV_PATH)
        extra = "ignore"


settings = Settings()
