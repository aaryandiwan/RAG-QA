# RAG-QA: Complete Architecture & Interview Study Guide 🧠📄

Yeh document aapke is project ka complete **Technical Blueprint & Study Guide** hai. Isme sab kuch aasan Hindi/Hinglish me explain kiya gaya hai taaki aap samajh sakein ki code me kya ho raha hai aur interview me ise kaise confidently explain karna hai.

---

## 1. 60-Second Interview Elevator Pitch

> *"Maine ek 100% pure Python Retrieval-Augmented Generation (RAG) system banaya hai jiska naam **RAG-QA** hai. Yeh system multi-format documents (PDF, DOCX, TXT, MD) ko parse karta hai, chunks me split karke 3072-dimensional vector embeddings banata hai aur Pinecone Serverless database me index karta hai.*
>
> *User ke sawal par yeh semantic similarity search karke top relevant chunks retrieve karta hai aur Google Gemini ke through context-grounded answer generate karta hai with transparent source citations (document name + page number). Maine isme BYOK (Bring-Your-Own-Key) security architecture aur rate-limit resilience bhi implement kiya hai, aur yeh live Streamlit Community Cloud par deployed hai."*

---

## 2. Current Architecture: End-to-End Working Flow

```
[User uploads Document: PDF/DOCX/TXT/MD]
                    │
                    ▼
          [1. Document Parser]
  (PyPDF / python-docx extracts raw text per page)
                    │
                    ▼
          [2. Recursive Text Chunking]
  (Chunk size: 500 chars, Overlap: 50 chars)
  (Overlap isliye rakha taaki sentence ka context na toote)
                    │
                    ▼
          [3. Embedding Generation]
  (Google Gemini Embedding 2 / candidate fallback)
  (Text chunks ko 3072 floating numbers ke vectors me convert karta hai)
                    │
                    ▼
          [4. Vector Storage]
  (Pinecone Serverless DB - AWS us-east-1)
  (Vectors metadata ke sath store hote hain: filename, page, text)
                    │
                    ▼
         ════════ User Asks Question ════════
                    │
                    ▼
          [5. Question Embedding & Top-K Retrieval]
  (Question ka vector banakar Pinecone me Cosine Similarity se
   top 5 best matching chunks retrieve kiye jaate hain)
                    │
                    ▼
          [6. LLM Grounded Generation]
  (Google Gemini 3.5 Flash Lite prompt me retrieved context + question
   padh kar answer generate karta hai)
                    │
                    ▼
          [7. Transparent Citations Output]
  (User ko clean answer ke sath exact Page Number aur Document Snippet dikhta hai)
```

---

## 3. Key Technical Challenges Jo Humne Solve Kiye (Interview Points)

### Challenge 1: Gemini Free Tier 429 Quota Exhaustion (Limit 1,000)
- **Problem:** Gemini ke model `gemini-embedding-001` par daily 1,000 requests ka limit tha. Jab 100+ pages ki file aati thi to har chunk par API call hone se limit khatam ho jaati thi (`Please retry in 3h51m`).
- **Solution:** 
  1. Humne **Batch Embedding** lagaya (ek API call me 20 chunks ek sath jaate hain).
  2. Automatic **Fallback Hierarchy** banayi: Pehle `gemini-embedding-2` try karega, fir `gemini-embedding-2-preview`, fir `gemini-embedding-001`.
  3. Exponential backoff retry logic lagaya jo rate limits ko gracefully handle karta hai.

### Challenge 2: BYOK (Bring-Your-Own-Key) Architecture
- **Problem:** Agar developer apni API keys code me ya server par hardcode kar de, to koi bhi public user use karke developer ke saare credits khatam kar dega ya key leak ho sakti hai.
- **Solution:** Streamlit Cloud par humne **BYOK Architecture** banaya. User sidebar me apni personal free keys daalta hai, jo sirf uske browser session memory me rehti hain aur kabhi bhi disk ya database me save nahi hoti.

### Challenge 3: Monolithic 100% Pure Python Migration
- **Problem:** Pehle project me React frontend (Node.js, Vite, npm, Tailwind) aur FastAPI backend alag the, jisko run karne ke liye 2 terminal, node_modules aur Docker lagta tha.
- **Solution:** Saara non-Python code delete karke Streamlit + LangChain + Python core me merge kiya. Isse GitHub par repo 100% Python ban gayi aur 1-click execution (`run_local.bat`) ready ho gaya.

---

## 4. Proposed Ollama Qwen Integration (Blueprint & Planned Changes)

Jab aap bolenge, tab hum ye changes step-by-step implement karenge:

### Change 1: `streamlit_app.py` me Model Selector
Sidebar me ek clean switch add hoga:
```python
model_provider = st.radio(
    "AI Engine Provider",
    ["Google Gemini (Cloud)", "Ollama Qwen 2.5 (Local)"],
    index=0
)
```
- **Jab Gemini select hoga:** Gemini aur Pinecone key inputs dikhenge.
- **Jab Ollama select hoga:** Key inputs hide ho jayenge aur status aayega: `🟢 Connected to Local Ollama (qwen2.5:3b)`.

### Change 2: Query Handler me Dual Routing
Jab user question puchega, system provider ke according route karega:
```python
if model_provider == "Ollama Qwen 2.5 (Local)":
    # Local Qwen generates the answer using retrieved context
    answer = ollama_generate(prompt=prompt, context=retrieved_context)
else:
    # Google Gemini generates the answer
    answer = gemini_generate(prompt=prompt, context=retrieved_context)
```

### Change 3: `requirements.txt`
Lightweight Python Ollama client:
```txt
ollama>=0.3.0
```

---

## 5. Important Terms Aapko Interview ke Liye Yaad Rakhne Hain

| Term | Simple Meaning |
| :--- | :--- |
| **RAG** | Retrieval-Augmented Generation — LLM ko internet/apne data se bahar ke private documents padhakar answer dilwana. |
| **Chunking** | Badi PDF ko 500-500 characters ke chote tukdon me todna taaki LLM ke context limit me fit ho sake. |
| **Embedding** | Text ko numbers ke mathematical vector me convert karna taaki computer meaning samajh sake. |
| **Cosine Similarity** | Do vectors ke beech ka angle check karna (jitna chota angle, utna zyada related text). |
| **Pinecone** | Cloud Vector Database jo millions of vectors me se microsecond me search karta hai. |
| **Ollama** | Local tool jo aapke apne computer ke hardware par open-source models (like Qwen, Llama) run karta hai. |
