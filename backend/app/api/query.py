import logging
from fastapi import APIRouter, HTTPException
from app.models.schemas import QueryRequest, QueryResponse
from app.services.rag_service import get_rag_service

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post("/", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Ask a question against uploaded documents.
    Optionally filter by specific document_ids.
    Supports multi-turn conversation via conversation_history.
    """
    if not request.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    logger.info(f"Query received: '{request.question[:80]}...'")

    try:
        service = get_rag_service()
        response = service.query(
            question=request.question,
            document_ids=request.document_ids,
            conversation_history=request.conversation_history,
            top_k=request.top_k,
        )
        return response
    except HTTPException:
        raise
    except RuntimeError as e:
        logger.exception("RAG service unavailable during query")
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Query processing failed")
        raise HTTPException(status_code=500, detail="Query processing failed.") from e
