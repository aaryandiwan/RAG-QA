# RAG-QA — Document Intelligence 🧠📄

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://rag-application26.streamlit.app)
[![Python](https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Google Gemini](https://img.shields.io/badge/Google%20Gemini-3.5%20Flash%20Lite-4285F4.svg?logo=google&logoColor=white)](https://ai.google.dev/)
[![Pinecone](https://img.shields.io/badge/Pinecone-Serverless%20(3072d)-000000.svg?logo=pinecone&logoColor=white)](https://www.pinecone.io/)
[![LangChain](https://img.shields.io/badge/LangChain-0.2.0-1C3C3C.svg?logo=langchain&logoColor=white)](https://www.langchain.com/)

A **100% Pure Python** Retrieval-Augmented Generation (RAG) application built with **Streamlit**, **Google Gemini**, and **Pinecone Serverless**. Upload documents (PDF, DOCX, TXT, MD) and chat with them in real time with transparent source citations.

---

## 🌐 Live Demo & Deployment

| Platform | Link | Status |
| :--- | :--- | :--- |
| ☁️ **Streamlit Community Cloud** | [**rag-application26.streamlit.app**](https://rag-application26.streamlit.app) | 🟢 **Live 24/7** (No installation needed) |
| 💻 **Localhost (Streamlit)** | [**http://localhost:8501**](http://localhost:8501) | Run via `run_local.bat` or `streamlit run streamlit_app.py` |

---

## ✨ Key Features

- 🐍 **100% Pure Python**: Clean, monolithic Python codebase without any JavaScript or Node.js dependencies.
- 🔑 **Bring Your Own Key (BYOK)**: Secure session-level API key input in the sidebar — zero server-side leaks and \$0 developer hosting cost.
- 📑 **Multi-Format Ingestion**: Supports `.pdf`, `.docx`, `.txt`, and `.md` files up to 20MB.
- ⚡ **Ultra-Fast Generation**: Powered by **Google Gemini 3.5 Flash Lite** for lightning-fast sub-2s responses.
- 🌲 **High-Dimensional Vector Search**: **Pinecone Serverless** vector database indexing with **3072-dimensional** embeddings (`models/gemini-embedding-2` with automatic quota fallback).
- 🎯 **Verifiable Source Citations**: Every answer includes expandable references detailing exact document names, page numbers, and matched context snippets.
- 💬 **Multi-Turn Chat History**: Interactive conversational memory across question-and-answer turns.

---

## 🛠️ Architecture

```mermaid
graph TD
    User([User in Browser]) -->|Upload & Chat| Streamlit["Streamlit UI (streamlit_app.py)"]
    
    subgraph Python Core ["Pure Python RAG Pipeline"]
        Streamlit --> Parser["Document Parser (PyPDF / python-docx)"]
        Parser --> Splitter["RecursiveCharacterTextSplitter (500 chars, 50 overlap)"]
        Splitter --> RAG["RAG Service Engine"]
    end

    subgraph Cloud AI ["Cloud AI Services"]
        RAG -->|Batch Embeddings (3072d)| GeminiEmb["Google Gemini Embedding 2"]
        RAG -->|Vector Upsert & Query| Pinecone["Pinecone Serverless DB (AWS us-east-1)"]
        RAG -->|Grounded Synthesis| GeminiLLM["Gemini 3.5 Flash Lite"]
    end
```

---

## 🚀 Local Setup & Installation

### Option 1: 1-Click Launch (Windows)

Simply double-click the included batch launcher:
```bat
run_local.bat
```
This automatically activates your Python virtual environment and opens [http://localhost:8501](http://localhost:8501) in your browser.

---

### Option 2: Manual Terminal Setup

#### 1. Clone the repository:
```bash
git clone https://github.com/aaryandiwan/RAG-QA.git
cd RAG-QA
```

#### 2. Create and activate a Python virtual environment:
```bash
python -m venv .venv

# Windows:
.venv\Scripts\activate

# Mac / Linux:
source .venv/bin/activate
```

#### 3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

#### 4. Run the Streamlit application:
```bash
streamlit run streamlit_app.py
```
Open **`http://localhost:8501`** in your browser, enter your free [Google Gemini API Key](https://aistudio.google.com/app/apikey) and [Pinecone API Key](https://app.pinecone.io/), upload your file, and start chatting!

---

## ⚙️ Environment Variables (Optional for Local Development)

If you prefer to load API keys automatically from a file instead of typing them in the sidebar, create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENV=us-east-1
PINECONE_INDEX=rag-qa-index
```

---

## 🧪 Testing

Run backend RAG pipeline unit tests:
```bash
pytest backend/tests/ -v
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.
