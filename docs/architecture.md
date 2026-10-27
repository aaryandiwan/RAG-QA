# Architecture & Deployment Guide 🧠📄

## Pure Python System Architecture

DocChat is a **100% Python** Retrieval-Augmented Generation (RAG) system powered by **Streamlit**, **LangChain**, **Google Gemini**, and **Pinecone Serverless**.

```
                   ┌─────────────────────────────────────────┐
                   │           Streamlit Web UI              │
                   │  (streamlit_app.py — Python 3.12)       │
                   │  - Drag & Drop Document Uploader        │
                   │  - BYOK (Bring Your Own Keys) Sidebar   │
                   │  - Interactive Markdown Chat UI         │
                   │  - Source Attribution & Citations       │
                   └──────────────────┬──────────────────────┘
                                      │ In-Process Python Call
                   ┌──────────────────▼──────────────────────┐
                   │           RAG Service Core              │
                   │  (app/services/rag_service.py)          │
                   │                                         │
                   │  - Chunking (RecursiveTextSplitter)     │
                   │  - Document Parsing (PyPDF, python-docx)│
                   │  - Embedding Generation & Fallback      │
                   │  - Pinecone Vector Indexing & Search    │
                   │  - Gemini Generative Response Stream    │
                   └──────────────────┬──────────────────────┘
                                      │
              ┌───────────────────────┴───────────────────────┐
              │                                               │
    ┌─────────▼────────┐                            ┌─────────▼────────┐
    │   Pinecone DB    │                            │  Google Gemini   │
    │ (Serverless 3072)│                            │ - Embedding 2    │
    │  AWS us-east-1   │                            │ - 3.5 Flash Lite │
    └──────────────────┘                            └──────────────────┘
```

---

## RAG Pipeline Detail

### Step 1: Document Indexing
```
File Upload (PDF / DOCX / TXT / MD)
    │
    ▼
parse_document()                 ← Extracts structured text per page or section
    │
    ▼
RecursiveCharacterTextSplitter   ← chunk_size=500, overlap=50
    │
    ▼
Google Gemini Embedding          ← 3072-dim vector per chunk
(gemini-embedding-2 / fallback)     Batch-processed with 429 exponential backoff
    │
    ▼
Pinecone Upsert                  ← Stored with metadata: {document_id, filename, page, text}
```

### Step 2: Query Answering
```
User Question
    │
    ▼
Embed Question                   ← Generates 3072-dim query vector
    │
    ▼
Pinecone Query (top_k=5)         ← Cosine similarity match over document index
    │
    ▼
Context Assembly                 ← Top-K context chunks combined into prompt
    │
    ▼
Gemini 3.5 Flash Lite            ← Context-grounded synthesis with transparent citations
```

---

## Deployment: Streamlit Community Cloud

The project is natively deployed on **Streamlit Community Cloud**:
- **Live URL:** [rag-application26.streamlit.app](https://rag-application26.streamlit.app)
- **Deployment Process:** Direct 1-click connection to GitHub `main` branch.
- **BYOK Architecture:** Users supply their own Gemini & Pinecone API keys in the sidebar. No server-side secrets are exposed or billed.
