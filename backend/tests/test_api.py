import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)


# ── Health Check ────────────────────────────────────────────────────

def test_health_check():
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


# ── Document Upload ─────────────────────────────────────────────────

@patch("app.api.documents.get_rag_service")
@patch("app.api.documents.parse_document")
def test_upload_txt_document(mock_parse, mock_get_rag):
    from langchain.schema import Document

    mock_parse.return_value = [Document(page_content="Hello world", metadata={})]
    mock_rag = MagicMock()
    mock_rag.index_document.return_value = 3
    mock_get_rag.return_value = mock_rag

    content = b"This is a test document for unit testing."
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.txt", content, "text/plain")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["filename"] == "test.txt"
    assert data["num_chunks"] == 3
    assert "document_id" in data


def test_upload_unsupported_format():
    response = client.post(
        "/api/documents/upload",
        files={"file": ("test.exe", b"binary content", "application/octet-stream")},
    )
    assert response.status_code == 400
    assert "Unsupported file type" in response.json()["detail"]


# ── Query ───────────────────────────────────────────────────────────

@patch("app.api.query.get_rag_service")
def test_query_returns_answer(mock_get_rag):
    from app.models.schemas import QueryResponse

    mock_rag = MagicMock()
    mock_rag.query.return_value = QueryResponse(
        answer="The document discusses machine learning.",
        sources=[],
        question="What is this document about?",
        model_used="gemini-2.0-flash",
    )
    mock_get_rag.return_value = mock_rag

    response = client.post("/api/query/", json={
        "question": "What is this document about?",
        "document_ids": None,
        "conversation_history": [],
        "top_k": 5,
    })

    assert response.status_code == 200
    assert "machine learning" in response.json()["answer"]


def test_query_empty_question():
    response = client.post("/api/query/", json={"question": "  "})
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()
