# Architecture & Deployment Guide

## System Architecture

RAG-QA is a pure Python Retrieval-Augmented Generation (RAG) system powered by Streamlit, LangChain, Pinecone Serverless, and a dual inference engine (Google Gemini Cloud + Ollama Local Qwen).

```
                   ┌─────────────────────────────────────────┐
                   │           Streamlit Web UI              │
                   │  (streamlit_app.py — Python 3.12)       │
                   │  - Drag & Drop Document Ingestion       │
                   │  - BYOK (Bring Your Own Keys) Sidebar   │
                   │  - Dual Engine Switch (Gemini / Ollama) │
                   │  - Smart Auto-Hide of Ollama on Cloud   │
                   │  - Source Attribution & Citations       │
                   └──────────────────┬──────────────────────┘
                                      │ In-Process Python Call
                   ┌──────────────────▼──────────────────────┐
                   │           RAG Service Core              │
                   │  (backend/app/services/rag_service.py)  │
                   │                                         │
                   │  - Continuous Multi-Page Parsing        │
                   │  - Chunking (1,500 chars, 250 overlap)  │
                   │  - Embedding Generation & Retry         │
                   │  - Pinecone Neighbor Expansion (#idx+1) │
                   └──────────────────┬──────────────────────┘
                                      │
              ┌───────────────────────┼───────────────────────┐
              │                       │                       │
    ┌─────────▼────────┐    ┌─────────▼────────┐    ┌─────────▼────────┐
    │   Pinecone DB    │    │  Google Gemini   │    │   Local Ollama   │
    │ (Serverless 3072)│    │ - Embedding 2    │    │ - Qwen 2.5       │
    │  AWS us-east-1   │    │ - 3.5 Flash Lite │    │ - Offline & Free │
    └──────────────────┘    └──────────────────┘    └──────────────────┘
```

---

## RAG Pipeline Detail

### Step 1: Document Indexing
```
File Upload (PDF / DOCX / TXT / MD)
    │
    ▼
parse_document()                 ← Continuous text extraction with [Page X] section tags
    │
    ▼
RecursiveCharacterTextSplitter   ← chunk_size=1500, overlap=250 (prevents list truncation)
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
Pinecone Query (top_k=8)         ← Cosine similarity match over document index
    │
    ▼
Neighbor Expansion               ← Automatically retrieves #idx+1 neighbor chunk continuation
    │
    ▼
Sequential Reading Sort          ← Sorts retrieved context by (document_id, chunk_index)
    │
    ▼
Context Assembly                 ← Natural reading order context assembled into prompt
    │
    ├─────────────────────────────┐
    ▼                             ▼
Google Gemini 3.5 Flash       Local Ollama (Qwen 2.5)
(Fast cloud generation)       (Zero limits, 100% private)
    │                             │
    └──────────────┬──────────────┘
                   │
                   ▼
       Grounded Answer with Source Citations
```

---

## Deployment: Streamlit Community Cloud

The project is natively deployed on Streamlit Community Cloud:
- Live URL: [rag-application26.streamlit.app](https://rag-application26.streamlit.app)
- Deployment Process: Connected directly to GitHub main branch with continuous integration.
- BYOK Architecture: Users supply their own Gemini & Pinecone API keys in the sidebar. No server-side secrets are exposed or billed.
- Smart Auto-Detection: On Streamlit Cloud containers, Ollama controls and offline warning alerts are automatically hidden, seamlessly defaulting visitors to Google Gemini.

