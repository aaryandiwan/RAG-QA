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

    def __init__(
        self,
        gemini_api_key: Optional[str] = None,
        pinecone_api_key: Optional[str] = None,
        pinecone_index: Optional[str] = None,
        pinecone_env: Optional[str] = None,
    ):
        self.gemini_api_key = gemini_api_key or settings.GEMINI_API_KEY
        self.pinecone_api_key = pinecone_api_key or settings.PINECONE_API_KEY
        self.pinecone_index = pinecone_index or settings.PINECONE_INDEX
        self.pinecone_env = pinecone_env or settings.PINECONE_ENV

        if not self.gemini_api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. Please provide your Gemini API key."
            )
        if not self.pinecone_api_key:
            raise RuntimeError(
                "PINECONE_API_KEY is not set. Please provide your Pinecone API key."
            )

        # Initialise Google Generative AI with REST transport
        genai.configure(api_key=self.gemini_api_key, transport="rest")
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL)

        # Initialise Pinecone
        logger.info(f"Connecting to Pinecone index: {self.pinecone_index}")
        self.pc = Pinecone(api_key=self.pinecone_api_key)
        self._ensure_index_exists()
        self.index = self.pc.Index(self.pinecone_index)

        # Verify dimension
        index_desc = self.pc.describe_index(self.pinecone_index)
        logger.info(
            f"Connected to index '{self.pinecone_index}' "
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

        if self.pinecone_index not in existing_names:
            self.pc.create_index(
                name=self.pinecone_index,
                dimension=settings.EMBEDDING_DIMENSION,
                metric="cosine",
                spec=ServerlessSpec(cloud="aws", region=self.pinecone_env),
            )
            logger.info(f"Created Pinecone index: {self.pinecone_index}")
            while not self.pc.describe_index(self.pinecone_index).status['ready']:
                time.sleep(1)
        else:
            # Check dimension of existing index
            index_desc = self.pc.describe_index(self.pinecone_index)
            if index_desc.dimension != settings.EMBEDDING_DIMENSION:
                error_msg = (
                    f"CRITICAL: Index '{self.pinecone_index}' has dimension "
                    f"{index_desc.dimension}, but embedding model requires "
                    f"{settings.EMBEDDING_DIMENSION}. Please delete the index in "
                    f"the Pinecone console or change PINECONE_INDEX."
                )
                logger.error(error_msg)
                raise RuntimeError(error_msg)

    def _embed_batch(self, texts: List[str], max_retries: int = 4) -> List[List[float]]:
        """
        Embed a batch of strings in a single API call with automatic model fallback
        and 429 retry backoff.
        """
        candidate_models = [
            settings.GEMINI_EMBEDDING_MODEL,
            "models/gemini-embedding-2",
            "models/gemini-embedding-2-preview",
            "models/gemini-embedding-001",
        ]
        # Remove duplicates while preserving order
        candidate_models = list(dict.fromkeys(candidate_models))

        for model_name in candidate_models:
            delay = 3
            for attempt in range(max_retries):
                try:
                    res = genai.embed_content(
                        model=model_name,
                        content=texts,
                    )
                    embeddings = res["embedding"]
                    if embeddings and isinstance(embeddings[0], list):
                        return embeddings
                    return [embeddings]
                except Exception as e:
                    err_str = str(e).lower()
                    # If daily quota exhausted on this model, switch to next model immediately
                    if "requestsperday" in err_str or "limit: 1000" in err_str:
                        logger.warning(
                            f"Daily quota exhausted on {model_name}. Switching to next embedding model..."
                        )
                        break
                    # If per-minute rate limit, back off and retry
                    elif ("429" in err_str or "quota" in err_str or "rate" in err_str) and attempt < max_retries - 1:
                        logger.warning(
                            f"Rate limit on {model_name} (attempt {attempt+1}/{max_retries}). "
                            f"Waiting {delay}s..."
                        )
                        time.sleep(delay)
                        delay = min(delay * 2, 30)
                    else:
                        if model_name == candidate_models[-1]:
                            logger.error(f"Embedding failed on all models: {e}")
                            raise e
                        break

    def _embed_text(self, text: str) -> List[float]:
        """Embed a single string with candidate model fallback."""
        return self._embed_batch([text])[0]

    def index_document(
        self,
        documents: List[Document],
        document_id: str,
        progress_callback: Optional[Any] = None,
    ) -> int:
        """
        Chunk documents and store embeddings in Pinecone using batch processing
        with rate-limit protection for large multi-hundred-page documents.
        """
        # Split documents into chunks
        chunks = self.text_splitter.split_documents(documents)
        total_chunks = len(chunks)
        logger.info(f"Indexing document {document_id}: total {total_chunks} chunks to process")

        batch_size = 40  # Embed 40 chunks per Gemini API call
        vectors = []

        for batch_start in range(0, total_chunks, batch_size):
            batch_chunks = chunks[batch_start : batch_start + batch_size]
            batch_texts = [c.page_content for c in batch_chunks]

            # Batch embed in 1 single API call
            embeddings = self._embed_batch(batch_texts)

            for j, (chunk, embedding) in enumerate(zip(batch_chunks, embeddings)):
                idx = batch_start + j
                chunk_id = f"{document_id}#{idx}"
                metadata = chunk.metadata.copy()
                metadata["text"] = chunk.page_content
                metadata["document_id"] = document_id

                vectors.append({
                    "id": chunk_id,
                    "values": embedding,
                    "metadata": metadata,
                })

            # Upsert into Pinecone in batches of 100
            if len(vectors) >= 100:
                self.index.upsert(vectors=vectors[:100])
                vectors = vectors[100:]

            # Update progress callback if provided
            processed = min(batch_start + batch_size, total_chunks)
            if progress_callback:
                try:
                    progress_callback(processed, total_chunks)
                except Exception:
                    pass

            # Gentle sleep between batch calls to stay well within free tier limits
            time.sleep(0.4)

        # Upsert any remaining vectors
        if vectors:
            self.index.upsert(vectors=vectors)

        logger.info(
            f"Successfully indexed document {document_id}: {total_chunks} chunks stored in Pinecone"
        )
        return total_chunks

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
