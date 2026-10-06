# RAG- (Q&A)🧠📄

A professional-grade Retrieval-Augmented Generation (RAG) application that allows users to upload documents and have intelligent, context-aware conversations with them. Powered by **Google Gemini** for reasoning and **Pinecone** for high-performance vector retrieval.

## ✨ Features

- **Multi-Format Support**: Seamlessly process PDF, DOCX, TXT, and Markdown files.
- **Intelligent RAG**: Uses `gemini-flash-latest` for lightning-fast, high-quality responses.
- **Source Citations**: Every answer includes direct references to the source document chunks, ensuring transparency and accuracy.
- **Contextual Memory**: Remembers your conversation history for natural, multi-turn interactions.
- **Modern UI**: A sleek, responsive interface built with React and Tailwind CSS, featuring glassmorphism and smooth animations.
- **Native Vector Integration**: Direct integration with Pinecone's native Python client for optimal performance.

## 🛠️ Tech Stack

### Frontend
- **Framework**: React 18 (Vite)
- **Styling**: Tailwind CSS
- **Icons**: Lucide React
- **Markdown**: React Markdown
- **API Client**: Axios

### Backend
- **Framework**: FastAPI (Python 3.12)
- **Orchestration**: LangChain
- **LLM**: Google Gemini 1.5 Flash
- **Embeddings**: Google Gemini Embedding (3072 dimensions)
- **Vector DB**: Pinecone (Serverless)
- **OCR/Parsing**: PyPDF, Unstructured, Python-Docx

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 18+
- [Google AI Studio API Key](https://aistudio.google.com/app/apikey)
- [Pinecone API Key](https://www.pinecone.io/)

### Local Setup

1. **Clone the Repository**
   ```bash
   git clone https://github.com/yourusername/rag-qa-project.git
   cd rag-qa-project
   ```

2. **Backend Configuration**
   ```bash
   cd backend
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
   Create a `.env` file in the `backend` folder:
   ```env
   GEMINI_API_KEY=your_gemini_key
   PINECONE_API_KEY=your_pinecone_key
   PINECONE_ENV=us-east-1
   PINECONE_INDEX=rag-qa-index-v1-3072
   ```

3. **Frontend Configuration**
   ```bash
   cd ../frontend
   npm install
   ```
   Create a `.env` file in the `frontend` folder:
   ```env
   VITE_API_URL=http://localhost:8082
   ```

4. **Run Locally**
   - **Backend**: `uvicorn main:app --reload --port 8082`
   - **Frontend**: `npm run dev`

---

## 🌍 Deployment Guide

### Backend: Railway.app

1. **Create New Project**: Select "Deploy from GitHub repo".
2. **Root Directory**: Set "Root Directory" to `backend`.
3. **Environment Variables**: Add all keys from your backend `.env`.
4. **Python Version**: Ensure Railway uses Python 3.12 by adding a `runtime.txt` with `python-3.12.3` or setting a variable.
5. **Port**: Railway automatically detects the port, but ensure `VITE_API_URL` on frontend matches the generated Railway URL.

### Frontend: Vercel

1. **Import Repository**: Connect your GitHub repo.
2. **Framework Preset**: Vite.
3. **Root Directory**: `frontend`.
4. **Environment Variables**: Add `VITE_API_URL` pointing to your deployed Railway backend (e.g., `https://your-backend.railway.app`).
5. **Build & Deploy**: Vercel will handle the rest!

## 📄 License
MIT License. Free to use and modify for personal and commercial projects.
