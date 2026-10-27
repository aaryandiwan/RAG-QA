import json
import logging
import urllib.request
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://127.0.0.1:11434"


def check_ollama_status(base_url: str = OLLAMA_BASE_URL, timeout: float = 2.0) -> Tuple[bool, List[str]]:
    """
    Check if a local Ollama instance is running and return available model tags.
    Returns:
        (is_online, list_of_models)
    """
    try:
        url = f"{base_url}/api/tags"
        req = urllib.request.Request(url, headers={"User-Agent": "RAG-QA"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "") for m in data.get("models", []) if m.get("name")]
                return True, models
    except Exception as e:
        logger.debug(f"Ollama status check failed: {e}")
    return False, []


def query_ollama(
    question: str,
    context_chunks: List[str],
    model: str = "qwen2.5:3b",
    base_url: str = OLLAMA_BASE_URL,
    timeout: float = 60.0,
) -> str:
    """
    Generate an answer using local Ollama model grounded in the retrieved document chunks.
    """
    context_text = "\n\n---\n\n".join(context_chunks)

    prompt = (
        "You are an intelligent document question-answering assistant. "
        "Answer the user's question accurately using ONLY the provided document context below. "
        "If the answer cannot be found in the context, clearly state that the provided documents do not contain this information.\n\n"
        f"Context from documents:\n{context_text}\n\n"
        f"Question: {question}\n\n"
        "Answer:"
    )

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0.2,
            "top_p": 0.9,
        }
    }).encode("utf-8")

    req = urllib.request.Request(
        f"{base_url}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"}
    )

    with urllib.request.urlopen(req, timeout=timeout) as resp:
        if resp.status == 200:
            result = json.loads(resp.read().decode("utf-8"))
            return result.get("response", "").strip()
        else:
            raise RuntimeError(f"Ollama returned HTTP status {resp.status}")
