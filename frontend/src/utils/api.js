import axios from "axios";

const API_URL = import.meta.env.VITE_API_URL
  || (typeof window !== "undefined" && window.location.hostname !== "localhost"
    ? window.location.origin
    : "http://localhost:8082");

const api = axios.create({ baseURL: API_URL });

// ── Documents ────────────────────────────────────────────────────

export const uploadDocument = async (file) => {
  const formData = new FormData();
  formData.append("file", file);
  const { data } = await api.post("/api/documents/upload", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
};

export const listDocuments = async () => {
  const { data } = await api.get("/api/documents/");
  return data;
};

export const deleteDocument = async (documentId) => {
  const { data } = await api.delete(`/api/documents/${documentId}`);
  return data;
};

// ── Query ────────────────────────────────────────────────────────

export const queryDocuments = async ({ question, documentIds, conversationHistory, topK = 5 }) => {
  const { data } = await api.post("/api/query/", {
    question,
    document_ids: documentIds || null,
    conversation_history: conversationHistory || [],
    top_k: topK,
  });
  return data;
};
