from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.api import documents, query, health
from app.core.config import settings
from app.core.logging import setup_logging

setup_logging()

app = FastAPI(
    title="RAG Document Q&A API",
    description="Upload documents and query them using natural language powered by GPT-4 + Pinecone.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    error_details = traceback.format_exc()
    print(f"GLOBAL ERROR: {exc}")
    print(error_details)
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "traceback": error_details},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "*",
            "Access-Control-Allow-Headers": "*",
        }
    )

app.include_router(health.router, prefix="/health", tags=["Health"])
app.include_router(documents.router, prefix="/api/documents", tags=["Documents"])
app.include_router(query.router, prefix="/api/query", tags=["Query"])


@app.get("/")
async def root():
    return {"message": "RAG Q&A API is running. Visit /docs for API reference."}
