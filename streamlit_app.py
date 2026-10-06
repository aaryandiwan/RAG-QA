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
    .key-card {
        background-color: #FFF7ED;
        border: 1px solid #FFEDD5;
        border-radius: 10px;
        padding: 14px;
        margin-bottom: 16px;
    }
</style>
""", unsafe_allow_html=True)

# Load backend imports
try:
    from app.core.config import settings
    from app.services.rag_service import RAGService
    from app.utils.document_parser import parse_document
except Exception as e:
    st.error(f"Error loading RAG backend: {e}")
    st.stop()

# Session State Initialization
if "messages" not in st.session_state:
    st.session_state.messages = []
if "indexed_docs" not in st.session_state:
    st.session_state.indexed_docs = {}  # {doc_id: {"filename": ..., "chunks": ...}}
if "rag_service" not in st.session_state:
    st.session_state.rag_service = None

# ── Sidebar: Bring Your Own Key (BYOK) ────────────────────────────────
with st.sidebar:
    st.title("⚙️ Setup & Upload")
    
    st.subheader("🔑 Your API Keys")
    st.caption("Enter your personal keys to use the app. Your keys are private to your session and never stored.")

    gemini_key = st.text_input(
        "Google Gemini API Key",
        value=st.session_state.get("user_gemini_key", ""),
        type="password",
        placeholder="AIzaSy...",
        help="Free key from Google AI Studio",
    )
    
    pinecone_key = st.text_input(
        "Pinecone API Key",
        value=st.session_state.get("user_pinecone_key", ""),
        type="password",
        placeholder="pcsk_...",
        help="Free key from Pinecone.io",
    )

    with st.expander("🛠️ Advanced Settings (Optional)"):
        pinecone_index = st.text_input(
            "Pinecone Index Name",
            value=st.session_state.get("user_pinecone_index", "rag-qa-index"),
            help="Name of your Pinecone index"
        )
        pinecone_env = st.text_input(
            "Pinecone Cloud Region",
            value=st.session_state.get("user_pinecone_env", "us-east-1"),
            help="Pinecone serverless region"
        )

    # Save to session state
    st.session_state["user_gemini_key"] = gemini_key.strip()
    st.session_state["user_pinecone_key"] = pinecone_key.strip()
    st.session_state["user_pinecone_index"] = pinecone_index.strip()
    st.session_state["user_pinecone_env"] = pinecone_env.strip()

    keys_ready = bool(st.session_state["user_gemini_key"] and st.session_state["user_pinecone_key"])

    if not keys_ready:
        st.markdown("""
        <div style="font-size:0.8rem; color:#78716C; margin-top:6px;">
            Need keys? Get them free here:<br/>
            • <a href="https://aistudio.google.com/app/apikey" target="_blank">Google AI Studio (Gemini)</a><br/>
            • <a href="https://app.pinecone.io/" target="_blank">Pinecone Console</a>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.success("✓ API Keys configured for this session!")

    st.markdown("---")
    st.subheader("📄 Upload Document")
    uploaded_file = st.file_uploader(
        "Upload PDF, DOCX, TXT, or MD",
        type=["pdf", "docx", "txt", "md"],
        help="Max file size 20MB",
        disabled=not keys_ready,
    )

    def get_user_rag_service():
        """Get or initialize RAG service with the current user's personal keys."""
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
            with st.spinner(f"Processing and indexing '{uploaded_file.name}' with your keys..."):
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
                            # Index document into user's Pinecone
                            service = get_user_rag_service()
                            doc_id = str(uuid.uuid4())
                            num_chunks = service.index_document(parsed_docs, doc_id)
                            
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
                        service = get_user_rag_service()
                        service.delete_document(doc_id)
                        del st.session_state.indexed_docs[doc_id]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Delete error: {e}")
    else:
        st.info("No documents indexed yet. Enter keys and upload above!")

    if st.button("🧹 Clear Chat History"):
        st.session_state.messages = []
        st.rerun()

# ── Main Chat Area ──────────────────────────────────────────────────
st.markdown('<div class="main-title">DocChat 🧠📄</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-title">Intelligent RAG Document Question Answering powered by Google Gemini & Pinecone</div>', unsafe_allow_html=True)

# If keys are missing, show prominent callout
if not keys_ready:
    st.info("👈 **Welcome to DocChat!** To get started, please enter your **Gemini API Key** and **Pinecone API Key** in the sidebar. Your keys are private to your session and never stored.")

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
chat_placeholder = "Ask a question about your uploaded documents..." if keys_ready else "Please enter your API keys in the sidebar first..."
if prompt := st.chat_input(chat_placeholder, disabled=not keys_ready):
    if not st.session_state.indexed_docs:
        st.warning("⚠️ Please upload and index at least one document from the sidebar first!")
    else:
        # Append User Message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Assistant Thinking & Streaming
        with st.chat_message("assistant"):
            with st.spinner("Searching document vectors & reasoning..."):
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
