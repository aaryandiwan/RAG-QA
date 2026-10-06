from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    num_chunks: int
    message: str


class DocumentInfo(BaseModel):
    document_id: str
    filename: str
    uploaded_at: datetime
    num_chunks: int
    file_type: str


class SourceChunk(BaseModel):
    content: str
    page: Optional[int] = None
    document_id: str
    filename: str
    score: float


class QueryRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None   # None = search all docs
    conversation_history: Optional[List[dict]] = []
    top_k: Optional[int] = 5


class QueryResponse(BaseModel):
    model_config = {"protected_namespaces": ()}

    answer: str
    sources: List[SourceChunk]
    question: str
    model_used: str
