# RAG-QA: Retrieval-Augmented Generation Document Assistant

RAG-QA is a pure Python document question-answering application. It allows you to upload documents (PDF, DOCX, TXT, Markdown) and chat with them using semantic search and grounded language models. 

The application supports a dual-engine architecture: you can run queries through Google Gemini in the cloud, or run completely offline using local open-source models through Ollama (such as Qwen 2.5) with zero API rate limits and zero cost.

---

## Live Deployment

- Public Web App: [rag-application26.streamlit.app](https://rag-application26.streamlit.app)
- Localhost URL: `http://localhost:8501`

---

## Core Capabilities

- Multi-Format Document Ingestion: Parses and extracts structured text from PDF, DOCX, TXT, and Markdown files up to 20MB.
- Dual Inference Engine:
  - Google Gemini 3.5 Flash: High-speed cloud generation with generous free-tier throughput.
  - Ollama Local (Qwen 2.5): 100% private, local GPU/CPU execution with unlimited tokens and zero quota limits.
- High-Dimensional Vector Search: Chunks text into 1,500-character segments with 250-character overlap using continuous cross-page assembly, generates 3072-dimensional vector embeddings, and performs top-K cosine similarity retrieval via Pinecone Serverless with sequential neighbor expansion.
- Verifiable Source Citations: Every answer references the source document name, page number, and matched text snippet to eliminate ungrounded hallucinations.
- Bring-Your-Own-Key (BYOK) Security: User API credentials are kept exclusively in transient browser session memory. No developer keys are exposed or billed.

---

## Architecture Flow

```
[User Document: PDF / DOCX / TXT / MD]
                  │
                  ▼
         [Document Parser]
  (Extracts continuous text with [Page X] headers)
                  │
                  ▼
     [Recursive Text Splitter]
  (1,500-char chunks with 250-char overlap)
                  │
                  ▼
     [Gemini Batch Embedding]
  (3072-dimensional vectors with rate-limit retry)
                  │
                  ▼
   [Pinecone Serverless Index]
  (AWS us-east-1 vector database)
                  │
                  ▼
       [User Asks a Question]
                  │
                  ▼
    [Cosine Similarity Search]
  (Pinecone retrieves top 8 chunks + neighbor expansion)
                  │
                  ├─────────────────────────────┐
                  ▼                             ▼
       [Google Gemini Cloud]         [Local Ollama (Qwen 2.5)]
                  │                             │
                  └──────────────┬──────────────┘
                                 │
                                 ▼
         [Grounded Answer + Verifiable Citations]
```

---

## Getting Started

### 1. Prerequisites

- Python 3.10 or higher
- A free [Google AI Studio API Key](https://aistudio.google.com/app/apikey)
- A free [Pinecone API Key](https://app.pinecone.io/)
- (Optional) [Ollama](https://ollama.com/) if you want to run open-source models locally without API limits.

---

### 2. Local Setup (Windows 1-Click Launch)

If you are on Windows, simply double-click:
```bat
run_local.bat
```
This batch script automatically activates the Python virtual environment and opens the Streamlit application at `http://localhost:8501`.

---

### 3. Manual Terminal Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/aaryandiwan/RAG-QA.git
   cd RAG-QA
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv

   # On Windows:
   .venv\Scripts\activate

   # On Linux/macOS:
   source .venv/bin/activate
   ```

3. Install required packages:
   ```bash
   pip install -r requirements.txt
   ```

4. (Optional) Create a `.env` file in the project root:
   ```env
   GEMINI_API_KEY=your_gemini_api_key_here
   PINECONE_API_KEY=your_pinecone_api_key_here
   PINECONE_ENV=us-east-1
   PINECONE_INDEX=rag-qa-index
   ```
   *Note: If `.env` is omitted, you can enter your keys directly in the web app sidebar.*

5. Launch the application:
   ```bash
   streamlit run streamlit_app.py
   ```

---

## Using Local Open-Source Models (Ollama)

To use local models like Qwen 2.5 without hitting API limits:

1. Download and install Ollama from [ollama.com](https://ollama.com).
2. Pull your preferred model in terminal:
   ```bash
   ollama run qwen2.5:3b
   ```
3. Open `http://localhost:8501`, switch the sidebar radio button to **Ollama Qwen (Local)**, and chat directly with your documents.

*Note on Cloud Deployments:* When hosted on Streamlit Community Cloud (e.g., `rag-application26.streamlit.app`), the application automatically detects that it is running in a cloud container without a local daemon and hides the Ollama options cleanly, defaulting to Google Gemini without displaying false-positive warning banners.

---

## Project Structure

```
RAG-QA/
├── backend/
│   ├── app/
│   │   ├── core/
│   │   │   ├── config.py             # App configuration, chunk sizing (1500 chars), API sanitization
│   │   │   └── logging.py            # Structured logging
│   │   ├── services/
│   │   │   ├── rag_service.py        # Core RAG engine, neighbor expansion, context sorting
│   │   │   └── ollama_service.py     # Local Ollama REST client & status probe
│   │   └── utils/
│   │       └── document_parser.py    # Cross-page continuous text parser (PDF, DOCX)
│   └── tests/
│       └── test_api.py               # Automated pytest suite
├── docs/
│   ├── architecture.md               # System design & component breakdown
│   └── PROJECT_GUIDE.md              # Technical blueprint and interview study guide
├── requirements.txt                  # Production Python dependencies
├── run_local.bat                     # Windows batch runner
└── streamlit_app.py                  # Main Streamlit web application
```

---

## Testing

Run unit tests across the RAG service components:
```bash
pytest backend/tests/ -v
```

---

## License

This project is licensed under the MIT License.
