import os
import sys
import tempfile
import uuid
import streamlit as st

# Ensure backend directory is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
backend_dir = os.path.join(current_dir, "backend")
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

# Page configuration
st.set_page_config(
    page_title="DocChat — RAG Document Q&A",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .main-title {
        font-size: 2.2rem;
        font-weight: 700;
        color: #EA580C;
        margin-bottom: 0.2rem;
    }
    .sub-title {
        color: #78716C;
        font-size: 1rem;
        margin-bottom: 1.5rem;
    }
    .source-box {
        background-color: #FFFBEB;
        border: 1px solid #FDE68A;
        border-radius: 8px;
        padding: 10px;
        margin-top: 8px;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

# Handle API keys from Streamlit Cloud Secrets or os.environ
try:
    if "GEMINI_API_KEY" in st.secrets:
        os.environ["GEMINI_API_KEY"] = st.secrets["GEMINI_API_KEY"]
    if "PINECONE_API_KEY" in st.secrets:
        os.environ["PINECONE_API_KEY"] = st.secrets["PINECONE_API_KEY"]
    if "PINECONE_ENV" in st.secrets:
        os.environ["PINECONE_ENV"] = st.secrets["PINECONE_ENV"]
    if "PINECONE_INDEX" in st.secrets:
        os.environ["PINECONE_INDEX"] = st.secrets["PINECONE_INDEX"]
except Exception:
    pass

# Load backend imports
try:
    from app.core.config import settings
    from app.services.rag_service import get_rag_service
    from app.utils.document_parser import parse_document
except Exception as e:
    st.error(f"Error loading RAG backend: {e}")
    st.stop()

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "indexed_docs" not in st.session_state:
    st.session_state.indexed_docs = {}  # {doc_id: {"filename": ..., "chunks": ...}}

# ── Sidebar ──────────────────────────────────────────────────────────
with st.sidebar:
    st.title("⚙️ Configuration & Upload")
    
    # API Keys Configuration fallback
    with st.expander("🔑 API Key Settings", expanded=not bool(settings.GEMINI_API_KEY and settings.PINECONE_API_KEY)):
        gemini_input = st.text_input(
            "Gemini API Key",
            value=settings.GEMINI_API_KEY,
            type="password",
            help="Get your free key from aistudio.google.com"
        )
        pinecone_input = st.text_input(
            "Pinecone API Key",
            value=settings.PINECONE_API_KEY,
            type="password",
            help="Get your key from app.pinecone.io"
        )
        if gemini_input:
            settings.GEMINI_API_KEY = gemini_input
            os.environ["GEMINI_API_KEY"] = gemini_input
        if pinecone_input:
            settings.PINECONE_API_KEY = pinecone_input
            os.environ["PINECONE_API_KEY"] = pinecone_input

    st.markdown("---")
    st.subheader("📄 Upload Document")
    uploaded_file = st.file_uploader(
        "Upload PDF, DOCX, TXT, or MD",
        type=["pdf", "docx", "txt", "md"],
        help="Max file size 20MB"
    )

    if uploaded_file is not None:
        file_key = f"uploaded_{uploaded_file.name}_{uploaded_file.size}"
        if file_key not in st.session_state:
            with st.spinner(f"Processing and indexing '{uploaded_file.name}'..."):
                try:
                    ext = uploaded_file.name.split(".")[-1].lower()
                    with tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}") as tmp_file:
                        tmp_file.write(uploaded_file.getvalue())
                        tmp_path = tmp_file.name

                    try:
                        # Parse document
                        parsed_docs = parse_document(tmp_path, uploaded_file.name)
                        if not parsed_docs:
                            st.error("Could not extract text from document.")
                        else:
                            # Index document into Pinecone
                            rag_service = get_rag_service()
                            doc_id = str(uuid.uuid4())
                            num_chunks = rag_service.index_document(parsed_docs, doc_id)
                            
                            st.session_state.indexed_docs[doc_id] = {
                                "filename": uploaded_file.name,
                                "chunks": num_chunks,
                            }
                            st.session_state[file_key] = True
                            st.success(f"✓ Indexed '{uploaded_file.name}' ({num_chunks} chunks)")
                    finally:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                except Exception as err:
                    st.error(f"Upload failed: {err}")

    # Indexed Documents List
    st.markdown("---")
    st.subheader(f"📚 Indexed Documents ({len(st.session_state.indexed_docs)})")
    if st.session_state.indexed_docs:
        for doc_id, info in list(st.session_state.indexed_docs.items()):
            col1, col2 = st.columns([4, 1])
            with col1:
                st.caption(f"📄 **{info['filename']}** ({info['chunks']} chunks)")
            with col2:
                if st.button("🗑️", key=f"del_{doc_id}", help=f"Delete {info['filename']}"):
                    try:
                        rag_service = get_rag_service()
                        rag_service.delete_document(doc_id)
                        del st.session_state.indexed_docs[doc_id]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete error: {e}")
    else:
        st.info("No documents indexed yet. Upload one above!")

    if st.button("🧹 Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# ── Main Chat Area ──────────────────────────────────────────────────
st.markdown('<div class="main-title">DocChat 🧠📄</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Intelligent RAG Document Question Answering powered by Google Gemini & Pinecone</div>', unsafe_allow_html=True)

# Display Chat Messages
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("sources"):
            with st.expander("📚 View Referenced Sources", expanded=False):
                for i, src in enumerate(msg["sources"], 1):
                    page_info = f" · Page {src['page']}" if src.get("page") else ""
                    st.markdown(f"**Source {i}: {src['filename']}{page_info}**")
                    st.caption(src["content"])
                    st.markdown("---")

# User Input
if prompt := st.chat_input("Ask a question about your uploaded documents..."):
    if not st.session_state.indexed_docs:
        st.warning("⚠️ Please upload and index at least one document from the sidebar first!")
    elif not (settings.GEMINI_API_KEY and settings.PINECONE_API_KEY):
        st.error("⚠️ API keys are missing. Please provide Gemini & Pinecone API keys in the sidebar.")
    else:
        # Append User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Assistant Thinking & Streaming
        with st.chat_message("assistant"):
            with st.spinner("Searching document vectors & reasoning..."):
                try:
                    rag_service = get_rag_service()
                    
                    # Convert conversation history
                    history = []
                    for i in range(0, len(st.session_state.messages) - 1, 2):
                        if i + 1 < len(st.session_state.messages):
                            history.append({
                                "human": st.session_state.messages[i]["content"],
                                "ai": st.session_state.messages[i+1]["content"]
                            })
                    
                    doc_ids = list(st.session_state.indexed_docs.keys())
                    result = rag_service.query(
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
                        with st.expander("📚 View Referenced Sources", expanded=False):
                            for i, src in enumerate(sources_data, 1):
                                page_info = f" · Page {src['page']}" if src.get("page") else ""
                                st.markdown(f"**Source {i}: {src['filename']}{page_info}**")
                                st.caption(src["content"])
                                st.markdown("---")

                    # Save to session history
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": result.answer,
                        "sources": sources_data
                    })

                except Exception as e:
                    error_msg = f"Sorry, an error occurred while processing: {e}"
                    st.error(error_msg)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": error_msg,
                        "sources": []
                    })
