import os
import uuid
import tempfile
import aiofiles
import logging
from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import List

import anyio
from app.core.config import settings
from app.models.schemas import DocumentUploadResponse
from app.services.rag_service import get_rag_service
from app.utils.document_parser import parse_document

router = APIRouter()
logger = logging.getLogger(__name__)

UPLOAD_DIR = os.path.join(tempfile.gettempdir(), "rag_uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

# In-memory store for demo (use a DB like PostgreSQL in production)
documents_store: dict = {}


@router.post("/upload", response_model=DocumentUploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """
    Upload a document, parse it, chunk it, embed it, and store in Pinecone.
    """
    # Validate file type
    ext = file.filename.split(".")[-1].lower()
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type '.{ext}'. Allowed: {settings.ALLOWED_EXTENSIONS}"
        )

    # Validate file size
    content = await file.read()
    size_mb = len(content) / (1024 * 1024)
    if size_mb > settings.MAX_FILE_SIZE_MB:
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({size_mb:.1f}MB). Max allowed: {settings.MAX_FILE_SIZE_MB}MB"
        )

    # Save file temporarily
    document_id = str(uuid.uuid4())
    temp_path = os.path.join(UPLOAD_DIR, f"{document_id}.{ext}")

    async with aiofiles.open(temp_path, "wb") as f:
        await f.write(content)

    try:
        # Parse document into LangChain Documents
        documents = parse_document(temp_path, file.filename)

        if not documents:
            raise HTTPException(status_code=422, detail="Could not extract text from document.")

        # Index into Pinecone (in threadpool so event loop is not blocked)
        service = get_rag_service()
        num_chunks = await anyio.to_thread.run_sync(service.index_document, documents, document_id)

        # Store metadata
        documents_store[document_id] = {
            "document_id": document_id,
            "filename": file.filename,
            "num_chunks": num_chunks,
            "file_type": ext,
        }

        logger.info(f"Uploaded and indexed '{file.filename}' as {document_id}")

        return DocumentUploadResponse(
            document_id=document_id,
            filename=file.filename,
            num_chunks=num_chunks,
            message=f"Successfully indexed '{file.filename}' into {num_chunks} chunks.",
        )

    except HTTPException:
        raise
    except RuntimeError as e:
        logger.exception("RAG service unavailable during upload")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Upload processing failed")
        raise HTTPException(status_code=500, detail="Document processing or indexing failed.") from e

    finally:
        # Clean up temp file
        if os.path.exists(temp_path):
            os.remove(temp_path)


@router.get("/", response_model=List[dict])
async def list_documents():
    """Return all uploaded documents."""
    return list(documents_store.values())


@router.delete("/{document_id}")
async def delete_document(document_id: str):
    """Delete a document and all its vectors from Pinecone."""
    if document_id not in documents_store:
        raise HTTPException(status_code=404, detail="Document not found.")

    try:
        service = get_rag_service()
        service.delete_document(document_id)
    except RuntimeError as e:
        logger.exception("RAG service unavailable during delete")
        raise HTTPException(status_code=503, detail=str(e))
    del documents_store[document_id]

    return {"message": f"Document {document_id} deleted successfully."}
