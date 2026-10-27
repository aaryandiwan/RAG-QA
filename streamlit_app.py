import os
import sys
import tempfile
import uuid
import streamlit as st

# Ensure backend directory and root directory are in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

# Page configuration
st.set_page_config(
    page_title="RAG-QA | Document Intelligence",
    page_icon="◆",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Premium Custom Styling (Clean, Executive, Enterprise SaaS aesthetic)
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Top brand header */
    .brand-wrapper {
        display: flex;
        align-items: baseline;
        gap: 12px;
        margin-bottom: 4px;
    }
    .brand-title {
        font-size: 2.2rem;
        font-weight: 700;
        letter-spacing: -0.03em;
        margin: 0;
        background: linear-gradient(135deg, #1E293B 0%, #475569 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    @media (prefers-color-scheme: dark) {
        .brand-title {
            background: linear-gradient(135deg, #F8FAFC 0%, #CBD5E1 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
    }
    .brand-badge {
        font-size: 0.72rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        padding: 3px 8px;
        border-radius: 6px;
        background: rgba(59, 130, 246, 0.1);
        color: #2563EB;
        border: 1px solid rgba(59, 130, 246, 0.25);
    }
    .brand-sub {
        font-size: 0.95rem;
        color: #64748B;
        margin-bottom: 24px;
        font-weight: 400;
    }

    /* Cards */
    .saas-card {
        border-radius: 10px;
        padding: 16px;
        margin-bottom: 16px;
        background: rgba(248, 250, 252, 0.8);
        border: 1px solid rgba(226, 232, 240, 0.8);
    }
    @media (prefers-color-scheme: dark) {
        .saas-card {
            background: rgba(30, 41, 59, 0.5);
            border: 1px solid rgba(51, 65, 85, 0.6);
        }
    }

    /* Info banner */
    .welcome-card {
        border-radius: 10px;
        padding: 16px 20px;
        background: rgba(238, 242, 255, 0.6);
        border: 1px solid rgba(199, 210, 254, 0.7);
        color: #3730A3;
        margin-bottom: 24px;
        font-size: 0.92rem;
        line-height: 1.5;
    }
    @media (prefers-color-scheme: dark) {
        .welcome-card {
            background: rgba(30, 27, 75, 0.4);
            border: 1px solid rgba(99, 102, 241, 0.3);
            color: #C7D2FE;
        }
    }

    /* Feature guides in empty state */
    .features-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
        gap: 14px;
        margin-top: 16px;
        margin-bottom: 28px;
    }
    .feature-item {
        padding: 16px;
        border-radius: 8px;
        background: rgba(241, 245, 249, 0.5);
        border: 1px solid rgba(226, 232, 240, 0.8);
    }
    @media (prefers-color-scheme: dark) {
        .feature-item {
            background: rgba(15, 23, 42, 0.4);
            border: 1px solid rgba(51, 65, 85, 0.5);
        }
    }
    .feature-step {
        font-size: 0.72rem;
        font-weight: 700;
        text-transform: uppercase;
        color: #2563EB;
        letter-spacing: 0.05em;
        margin-bottom: 4px;
    }
    .feature-title {
        font-size: 0.92rem;
        font-weight: 600;
        margin-bottom: 4px;
    }
    .feature-desc {
        font-size: 0.82rem;
        color: #64748B;
        line-height: 1.4;
    }

    /* Citation cards */
    .citation-card {
        padding: 12px 14px;
        border-radius: 8px;
        background: rgba(248, 250, 252, 0.8);
        border: 1px solid rgba(226, 232, 240, 0.9);
        margin-bottom: 10px;
    }
    @media (prefers-color-scheme: dark) {
        .citation-card {
            background: rgba(15, 23, 42, 0.5);
            border: 1px solid rgba(51, 65, 85, 0.6);
        }
    }
    .citation-badge {
        font-size: 0.72rem;
        font-weight: 600;
        padding: 2px 7px;
        border-radius: 4px;
        background: rgba(59, 130, 246, 0.12);
        color: #2563EB;
        display: inline-block;
        margin-bottom: 6px;
    }

    /* Refined buttons */
    div.stButton > button {
        border-radius: 7px;
        font-weight: 500;
        transition: all 0.15s ease;
    }
</style>
""", unsafe_allow_html=True)

# Load backend imports
try:
    from app.core.config import settings
    from app.services.rag_service import RAGService
    from app.utils.document_parser import parse_document
except Exception as e:
    st.error(f"Error loading RAG backend core: {e}")
    st.stop()

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "indexed_docs" not in st.session_state:
    st.session_state.indexed_docs = {}
if "rag_service" not in st.session_state:
    st.session_state.rag_service = None

# ── Sidebar: API Credentials & Documents ──────────────────────────────
with st.sidebar:
    st.markdown("### Configuration")
    st.caption("Provide your credentials to establish an isolated session.")

    gemini_key = st.text_input(
        "Google Gemini API Key",
        value=st.session_state.get("user_gemini_key", ""),
        type="password",
        placeholder="AIzaSy...",
        help="Obtain free key from Google AI Studio",
    )
    
    pinecone_key = st.text_input(
        "Pinecone API Key",
        value=st.session_state.get("user_pinecone_key", ""),
        type="password",
        placeholder="pcsk_...",
        help="Obtain free key from Pinecone Console",
    )

    with st.expander("Advanced Settings"):
        pinecone_index = st.text_input(
            "Pinecone Index Name",
            value=st.session_state.get("user_pinecone_index", "rag-qa-index"),
            help="Target Pinecone index name"
        )
        pinecone_env = st.text_input(
            "Cloud Region",
            value=st.session_state.get("user_pinecone_env", "us-east-1"),
            help="Pinecone Serverless deployment region"
        )

    # Save to session state
    st.session_state["user_gemini_key"] = gemini_key.strip()
    st.session_state["user_pinecone_key"] = pinecone_key.strip()
    st.session_state["user_pinecone_index"] = pinecone_index.strip()
    st.session_state["user_pinecone_env"] = pinecone_env.strip()

    keys_ready = bool(st.session_state["user_gemini_key"] and st.session_state["user_pinecone_key"])

    if not keys_ready:
        st.markdown("""
        <div style="font-size:0.8rem; color:#64748B; margin-top:8px; line-height:1.5;">
            Need free API keys?<br/>
            • <a href="https://aistudio.google.com/app/apikey" target="_blank" style="color:#2563EB; text-decoration:none;">Google AI Studio</a><br/>
            • <a href="https://app.pinecone.io/" target="_blank" style="color:#2563EB; text-decoration:none;">Pinecone Console</a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.caption("Active · Session keys configured")

    st.markdown("---")
    st.markdown("### Document Management")
    uploaded_file = st.file_uploader(
        "Ingest Knowledge Base",
        type=["pdf", "docx", "txt", "md"],
        help="Supported formats: PDF, DOCX, TXT, MD. Max 20MB.",
        disabled=not keys_ready,
    )

    def get_user_rag_service():
        """Get or initialize RAG service with the current session credentials."""
        if st.session_state.rag_service is None:
            st.session_state.rag_service = RAGService(
                gemini_api_key=st.session_state["user_gemini_key"],
                pinecone_api_key=st.session_state["user_pinecone_key"],
                pinecone_index=st.session_state.get("user_pinecone_index", "rag-qa-index"),
                pinecone_env=st.session_state.get("user_pinecone_env", "us-east-1"),
            )
        return st.session_state.rag_service

    if uploaded_file is not None and keys_ready:
        file_key = f"uploaded_{uploaded_file.name}_{uploaded_file.size}"
        if file_key not in st.session_state:
            with st.spinner(f"Ingesting '{uploaded_file.name}'..."):
                try:
                    ext = uploaded_file.name.split(".")[-1].lower()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name

                    try:
                        # Parse document
                        parsed_docs = parse_document(tmp_path, uploaded_file.name)
                        if not parsed_docs:
                            st.error("Document parsing failed: No extractable text detected.")
                        else:
                            service = get_user_rag_service()
                            doc_id = str(uuid.uuid4())

                            prog_bar = st.progress(0, text="Generating embeddings...")

                            def on_progress(current, total):
                                pct = min(int((current / total) * 100), 100)
                                prog_bar.progress(pct, text=f"Indexing: {current}/{total} chunks ({pct}%)...")

                            num_chunks = service.index_document(parsed_docs, doc_id, progress_callback=on_progress)
                            prog_bar.empty()
                            
                            st.session_state.indexed_docs[doc_id] = {
                                "filename": uploaded_file.name,
                                "chunks": num_chunks,
                            }
                            st.session_state[file_key] = True
                            st.success(f"Indexed '{uploaded_file.name}' ({num_chunks} chunks)")
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                except Exception as err:
                    st.error(f"Ingestion error: {err}")

    # Active Documents List
    st.markdown("---")
    st.markdown(f"### Active Documents ({len(st.session_state.indexed_docs)})")
    if st.session_state.indexed_docs:
        for doc_id, info in list(st.session_state.indexed_docs.items()):
            col1, col2 = st.columns([4, 1.2])
            with col1:
                st.caption(f"**{info['filename']}**  \n{info['chunks']} indexed chunks")
            with col2:
                if st.button("Delete", key=f"del_{doc_id}", help=f"Delete {info['filename']}"):
                    try:
                        service = get_user_rag_service()
                        service.delete_document(doc_id)
                        del st.session_state.indexed_docs[doc_id]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Deletion failed: {e}")
    else:
        st.caption("No documents currently indexed.")

    if st.session_state.messages:
        if st.button("Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.rerun()

# ── Main Workspace ──────────────────────────────────────────────────
st.markdown("""
<div class="brand-wrapper">
    <h1 class="brand-title">RAG-QA</h1>
    <span class="brand-badge">Enterprise Edition</span>
</div>
<div class="brand-sub">Grounded document intelligence powered by Gemini 3.5 Flash & Pinecone Vector Search</div>
""", unsafe_allow_html=True)

# Onboarding guide if keys not provided
if not keys_ready:
    st.markdown("""
    <div class="welcome-card">
        <strong>Getting Started</strong><br/>
        Enter your <strong>Google Gemini API Key</strong> and <strong>Pinecone API Key</strong> in the configuration sidebar to activate the reasoning engine. Your credentials remain strictly in memory and are never stored or logged.
    </div>
    <div class="features-grid">
        <div class="feature-item">
            <div class="feature-step">Phase 1</div>
            <div class="feature-title">Credentials</div>
            <div class="feature-desc">Input your Gemini and Pinecone keys in the sidebar.</div>
        </div>
        <div class="feature-item">
            <div class="feature-step">Phase 2</div>
            <div class="feature-title">Ingest</div>
            <div class="feature-desc">Upload PDF, DOCX, TXT, or Markdown documents for vector indexing.</div>
        </div>
        <div class="feature-item">
            <div class="feature-step">Phase 3</div>
            <div class="feature-title">Synthesize</div>
            <div class="feature-desc">Query your knowledge base with transparent source attribution.</div>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Display Chat Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander(f"Referenced Sources ({len(msg['sources'])})", expanded=False):
                for i, src in enumerate(msg["sources"], 1):
                    page_badge = f" · Page {src['page']}" if src.get("page") else ""
                    st.markdown(f"""
                    <div class="citation-card">
                        <span class="citation-badge">Source {i} — {src['filename']}{page_badge}</span>
                        <div style="font-size: 0.85rem; color: #475569; line-height: 1.45;">{src['content']}</div>
                    </div>
                    """, unsafe_allow_html=True)

# Chat Input Area
chat_placeholder = "Ask a question about your indexed knowledge base..." if keys_ready else "Configure API credentials in the sidebar to begin..."
if prompt := st.chat_input(chat_placeholder, disabled=not keys_ready):
    if not st.session_state.indexed_docs:
        st.warning("Please upload and index at least one document in the sidebar before querying.")
    else:
        # Append User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Assistant Thinking & Retrieval
        with st.chat_message("assistant"):
            with st.spinner("Retrieving relevant context and synthesizing..."):
                try:
                    service = get_user_rag_service()
                    
                    # Convert conversation history
                    history = []
                    for i in range(0, len(st.session_state.messages) - 1, 2):
                        if i + 1 < len(st.session_state.messages):
                            history.append({
                                "human": st.session_state.messages[i]["content"],
                                "ai": st.session_state.messages[i+1]["content"]
                            })
                    
                    doc_ids = list(st.session_state.indexed_docs.keys())
                    result = service.query(
                        question=prompt,
                        document_ids=doc_ids,
                        conversation_history=history,
                    )

                    st.markdown(result.answer)
                    
                    sources_data = [
                        {
                            "filename": s.filename,
                            "page": s.page,
                            "content": s.content
                        }
                        for s in result.sources
                    ]

                    if sources_data:
                        with st.expander(f"Referenced Sources ({len(sources_data)})", expanded=False):
                            for i, src in enumerate(sources_data, 1):
                                page_badge = f" · Page {src['page']}" if src.get("page") else ""
                                st.markdown(f"""
                                <div class="citation-card">
                                    <span class="citation-badge">Source {i} — {src['filename']}{page_badge}</span>
                                    <div style="font-size: 0.85rem; color: #475569; line-height: 1.45;">{src['content']}</div>
                                </div>
                                """, unsafe_allow_html=True)

                    # Save to session history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result.answer,
                        "sources": sources_data
                    })

                except Exception as e:
                    error_msg = f"An error occurred while processing your request: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "sources": []
                    })
