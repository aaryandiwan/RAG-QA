import logging
import uuid
import time
from typing import List, Optional, Any

import google.generativeai as genai
try:
    from langchain_text_splitters import RecursiveCharacterTextSplitter
except ImportError:
    from langchain.text_splitter import RecursiveCharacterTextSplitter

try:
    from langchain_core.documents import Document
except ImportError:
    from langchain.schema import Document

from pinecone import Pinecone, ServerlessSpec

from app.core.config import settings
from app.models.schemas import SourceChunk, QueryResponse

logger = logging.getLogger(__name__)


class RAGService:
    """
    Core RAG service handling:
    - Document chunking and embedding (via Gemini models/gemini-embedding-001)
    - Pinecone vector store indexing (via native client, 3072 dims)
    - Retrieval and Gemini answer generation (via models/gemini-3.8-flash)
    """

    def __init__(self):
        if not settings.GEMINI_API_KEY:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Please add it to your .env file."
            )
        if not settings.PINECONE_API_KEY:
            raise RuntimeError(
                "PINECONE_API_KEY is not set. Please add it to your .env file."
            )

        # Initialise Google Generative AI with REST transport
        genai.configure(api_key=settings.GEMINI_API_KEY, transport="rest")
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

        # Initialise Pinecone
        logger.info(f"Connecting to Pinecone index: {settings.PINECONE_INDEX}")
        self.pc = Pinecone(api_key=settings.PINECONE_API_KEY)
        self._ensure_index_exists()
        self.index = self.pc.Index(settings.PINECONE_INDEX)

        # Verify dimension
        index_desc = self.pc.describe_index(settings.PINECONE_INDEX)
        logger.info(
            f"Connected to index '{settings.PINECONE_INDEX}' "
            f"with dimension {index_desc.dimension}"
        )

        # Text splitter for chunking
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

        logger.info("RAGService initialised successfully")

    def _ensure_index_exists(self):
        """Create Pinecone index if it doesn't exist."""
        existing_indexes = self.pc.list_indexes()
        existing_names = [i.name for i in existing_indexes]

        if settings.PINECONE_INDEX not in existing_names:
            self.pc.create_index(
                name=settings.PINECONE_INDEX,
                dimension=settings.EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=settings.PINECONE_ENV),
            )
            logger.info(f"Created Pinecone index: {settings.PINECONE_INDEX}")
            while not self.pc.describe_index(settings.PINECONE_INDEX).status['ready']:
                time.sleep(1)
        else:
            # Check dimension of existing index
            index_desc = self.pc.describe_index(settings.PINECONE_INDEX)
            if index_desc.dimension != settings.EMBEDDING_DIMENSION:
                error_msg = (
                    f"CRITICAL: Index '{settings.PINECONE_INDEX}' has dimension "
                    f"{index_desc.dimension}, but embedding model requires "
                    f"{settings.EMBEDDING_DIMENSION}. Please delete the index in "
                    f"the Pinecone console or change PINECONE_INDEX in your .env."
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)

    def _embed_text(self, text: str) -> List[float]:
        """Embed a single string using Gemini embedding model."""
        res = genai.embed_content(
            model=settings.GEMINI_EMBEDDING_MODEL,
            content=text,
        )
        return res["embedding"]

    def index_document(self, documents: List[Document], document_id: str) -> int:
        """
        Chunk documents and store embeddings in Pinecone using native client.
        """
        # Split documents into chunks
        chunks = self.text_splitter.split_documents(documents)

        # Prepare vectors for upsert
        vectors = []
        for i, chunk in enumerate(chunks):
            chunk_id = f"{document_id}#{i}"
            embedding = self._embed_text(chunk.page_content)
            metadata = chunk.metadata.copy()
            metadata["text"] = chunk.page_content
            metadata["document_id"] = document_id

            vectors.append({
                "id": chunk_id,
                "values": embedding,
                "metadata": metadata,
            })

        # Upsert in batches of 100
        batch_size = 100
        try:
            for i in range(0, len(vectors), batch_size):
                batch = vectors[i : i + batch_size]
                self.index.upsert(vectors=batch)
        except Exception as e:
            logger.error(f"Pinecone upsert failed: {e}")
            raise

        logger.info(
            f"Indexed document {document_id}: {len(chunks)} chunks stored in Pinecone"
        )
        return len(chunks)

    def query(
        self,
        question: str,
        document_ids: Optional[List[str]] = None,
        conversation_history: Optional[List[dict]] = None,
        top_k: int = 5,
    ) -> QueryResponse:
        """
        Answer a question using RAG with direct retrieval + prompt approach.
        """
        # 1. Embed the query
        query_vector = self._embed_text(question)

        # 2. Build optional document filter
        search_filter = None
        if document_ids:
            search_filter = {"document_id": {"$in": document_ids}}

        # 3. Query Pinecone
        results = self.index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=search_filter,
        )

        # 4. Extract retrieved chunks
        retrieved_docs = []
        for match in results.get("matches", []):
            metadata = match.get("metadata", {})
            retrieved_docs.append({
                "text": metadata.get("text", ""),
                "filename": metadata.get("filename", ""),
                "page": metadata.get("page"),
                "document_id": metadata.get("document_id", ""),
                "score": match.get("score", 0.0),
            })

        # 5. Build context string from retrieved chunks
        context_parts = []
        for i, doc in enumerate(retrieved_docs, 1):
            page_info = f" (page {doc['page']})" if doc.get("page") else ""
            context_parts.append(
                f"[Source {i}: {doc['filename']}{page_info}]\n{doc['text']}"
            )
        context = "\n\n---\n\n".join(context_parts) if context_parts else "No relevant context found."

        # 6. Build conversation history string
        history_str = ""
        if conversation_history:
            history_parts = []
            for turn in conversation_history:
                human = turn.get("human", "")
                ai = turn.get("ai", "")
                if human:
                    history_parts.append(f"User: {human}")
                if ai:
                    history_parts.append(f"Assistant: {ai}")
            history_str = "\n".join(history_parts)

        # 7. Build the prompt
        prompt = self._build_prompt(question, context, history_str)

        # 8. Call Gemini
        response = self.model.generate_content(prompt)
        answer = response.text

        # 9. Build source chunks for response
        sources = []
        seen = set()
        for doc in retrieved_docs:
            key = doc["text"][:100]
            if key not in seen:
                seen.add(key)
                content = doc["text"][:300]
                if len(doc["text"]) > 300:
                    content += "..."
                sources.append(SourceChunk(
                    content=content,
                    page=doc.get("page"),
                    document_id=doc.get("document_id", ""),
                    filename=doc.get("filename", ""),
                    score=doc.get("score", 0.0),
                ))

        return QueryResponse(
            answer=answer,
            sources=sources,
            question=question,
            model_used=settings.GEMINI_MODEL,
        )

    def _build_prompt(self, question: str, context: str, history: str) -> str:
        """Build the RAG prompt for Gemini."""
        parts = [
            "You are a helpful document Q&A assistant. Answer the user's question "
            "based ONLY on the provided document context below. If the context does "
            "not contain enough information to answer, say so clearly. Always cite "
            "which source(s) you used.",
            "",
            "## Document Context",
            context,
        ]

        if history:
            parts.extend([
                "",
                "## Conversation History",
                history,
            ])

        parts.extend([
            "",
            "## Current Question",
            question,
            "",
            "## Your Answer",
        ])

        return "\n".join(parts)

    def delete_document(self, document_id: str):
        """Delete all chunks for a document from Pinecone."""
        self.index.delete(filter={"document_id": {"$eq": document_id}})
        logger.info(f"Deleted document {document_id} from Pinecone")


# ── Lazy singleton ──────────────────────────────────────────────────
_rag_service: Optional[RAGService] = None


def get_rag_service() -> RAGService:
    """Return the RAGService singleton, creating it on first call."""
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
