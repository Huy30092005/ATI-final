"""
ARA (AI Research Assistant) - FastAPI Application Entry Point.
Provides high-performance RESTful API endpoints for the research assistant pipeline,
LangChain orchestration, and multi-source evidence synthesis.
"""

import re
import time
import uuid
import asyncio
import logging
from collections import OrderedDict
from contextlib import asynccontextmanager
from typing import List, Optional, Dict, Any, Literal

from fastapi import FastAPI, UploadFile, File, HTTPException, Response, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel, Field

from backend.config import settings
from backend.schemas import (
    ResearchQueryRequest,
    ResearchQueryResponse,
    IndexedDocument,
    ChatMessage,
    SourceEvidence,
    ApiHealthResponse,
)
from backend.services.orchestrator import ResearchOrchestrator
from backend.services.document_loader import DocumentLoaderService, DocumentError, DOCUMENT_STORE
from backend.services.vector_store import vector_store
from backend.services import exporter

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger("ara.backend")

orchestrator: Optional[ResearchOrchestrator] = None
doc_loader: Optional[DocumentLoaderService] = None

# Short-term chat memory per session id (bounded, in-memory)
SESSIONS: "OrderedDict[str, List[ChatMessage]]" = OrderedDict()
MAX_SESSIONS = 200
MAX_HISTORY_MESSAGES = 12


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes singleton services on startup."""
    global orchestrator, doc_loader
    logger.info("Starting ARA (AI Research Assistant) FastAPI Backend...")
    orchestrator = ResearchOrchestrator()
    doc_loader = DocumentLoaderService()

    # Pre-seed sample academic reference paper if store is empty
    if not DOCUMENT_STORE:
        sample_paper_text = """Title: Attention Is All You Need (Vaswani et al., 2017)
The dominant sequence transduction models are based on complex recurrent or convolutional neural networks that include an encoder and a decoder. The best performing models also connect the encoder and decoder through an attention mechanism. We propose a new simple network architecture, the Transformer, based solely on attention mechanisms, dispensing with recurrence and convolutions entirely. Experiments on two machine translation tasks show these models to be superior in quality while being more parallelizable and requiring significantly less time to train.

On the WMT 2014 English-to-German translation task, the big transformer model achieves 28.4 BLEU, improving over the existing best results, including ensembles, by over 2 BLEU. On the WMT 2014 English-to-French translation task, our model establishes a new single-model state-of-the-art BLEU score of 41.8 after training for 3.5 days on eight GPUs.

Self-attention, sometimes called intra-attention, is an attention mechanism relating different positions of a single sequence in order to compute a representation of the sequence. Self-attention has been used successfully in a variety of tasks including reading comprehension, abstractive summarization, textual entailment and learning task-independent sentence representations."""
        doc_loader.process_and_index_document(
            filename="Attention_Is_All_You_Need_Reference.txt",
            file_bytes=sample_paper_text.encode("utf-8"),
            file_type="txt",
        )
        logger.info("Pre-seeded reference paper into document knowledge base.")

    yield
    logger.info("Shutting down ARA FastAPI Backend...")


app = FastAPI(
    title=settings.APP_NAME,
    description="High-performance backend for ARA (AI Research Assistant). Integrates LangChain orchestration, OpenAI LLM synthesis, multi-source academic/web searching, and automated evidence quality scoring.",
    version="1.0.0",
    lifespan=lifespan,
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
async def root():
    return {
        "name": settings.APP_NAME,
        "status": "online",
        "docs_url": "/docs",
        "api_v1": "/api",
        "message": "ARA Backend is operational. Connect the React frontend or call /api/research/query.",
    }


@app.get("/api/health", response_model=ApiHealthResponse, tags=["System"])
async def get_health():
    """Health check endpoint checking integrations."""
    return ApiHealthResponse(
        status="healthy",
        backend_engine="fastapi_python",
        openai_configured=bool(settings.OPENAI_API_KEY and len(settings.OPENAI_API_KEY) > 5),
        mongodb_configured=vector_store.is_connected(),
        search_provider=settings.SEARCH_PROVIDER,
        version="1.0.0",
    )


@app.post("/api/research/query", response_model=ResearchQueryResponse, tags=["Research"])
async def run_research_query(request: ResearchQueryRequest):
    """Full-detail research endpoint (rich response with pipeline trace and metrics)."""
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")
    try:
        return await orchestrator.execute_research(request)
    except Exception as e:
        logger.exception("Research execution failed")
        raise HTTPException(status_code=500, detail=f"Research synthesis error: {e}")


# ---------------------------------------------------------------------------
# Frontend contract (see frontend/src/api/research.js)
# ---------------------------------------------------------------------------

def _doc_to_api(doc: IndexedDocument) -> Dict[str, Any]:
    return {"id": doc.id, "name": doc.name, "size": doc.size_bytes, "status": doc.status, "chunks": doc.chunk_count}


_EVIDENCE_TYPE = {"uploaded_doc": "document", "live_web": "web", "academic_db": "academic"}


def _evidence_to_api(ev: SourceEvidence) -> Dict[str, Any]:
    return {
        "id": ev.id,
        "source_type": _EVIDENCE_TYPE.get(ev.source_type, "web"),
        "title": ev.title,
        "url": None if ev.url.startswith("document://") else ev.url,
        "authors": ev.authors or None,
        "year": ev.published_year,
        "snippet": ev.snippet,
        "relevance": ev.relevance_score,
        "credibility": ev.credibility_score,
    }


@app.get("/api/documents", tags=["Documents"])
async def list_documents():
    return [_doc_to_api(d) for d in DOCUMENT_STORE.values()]


@app.post("/api/documents", tags=["Documents"])
async def upload_document(file: UploadFile = File(...)):
    """Accepts a PDF or TXT file; rejects scanned PDFs, empty, oversized and unsupported files."""
    if not doc_loader:
        raise HTTPException(status_code=500, detail="Document loader not initialized")

    filename = file.filename or "uploaded_document"
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if ext not in ("pdf", "txt"):
        raise HTTPException(status_code=415, detail="Unsupported file type. Upload a PDF or TXT file.")

    limit = settings.MAX_UPLOAD_MB * 1024 * 1024
    file_bytes = await file.read(limit + 1)  # never buffer more than limit + 1 byte
    if len(file_bytes) > limit:
        raise HTTPException(status_code=413, detail=f"File is larger than the {settings.MAX_UPLOAD_MB} MB limit.")

    try:
        # PDF parsing + embedding are blocking -> worker thread
        doc = await asyncio.to_thread(doc_loader.process_and_index_document, filename, file_bytes, ext)
    except DocumentError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception:
        logger.exception("Upload processing failed")
        raise HTTPException(status_code=500, detail="Failed to process the document.")
    return _doc_to_api(doc)


@app.delete("/api/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Documents"])
async def delete_document(doc_id: str):
    if not doc_loader or not await asyncio.to_thread(doc_loader.delete_document, doc_id):
        raise HTTPException(status_code=404, detail="Document not found.")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


class ChatSources(BaseModel):
    documents: bool = True
    web: bool = True
    academic: bool = True


class ChatRequest(BaseModel):
    session_id: Optional[str] = None
    message: str = Field(..., min_length=3)
    document_ids: List[str] = Field(default_factory=list)
    sources: ChatSources = Field(default_factory=ChatSources)


@app.post("/api/chat", tags=["Research"])
async def chat(req: ChatRequest):
    if not orchestrator:
        raise HTTPException(status_code=500, detail="Orchestrator not initialized")

    sid = req.session_id or uuid.uuid4().hex
    history = SESSIONS.get(sid, [])
    search_sources = [
        name for name, on in (
            ("uploaded_docs", req.sources.documents),
            ("live_web", req.sources.web),
            ("academic_db", req.sources.academic),
        ) if on
    ]
    if not search_sources:
        raise HTTPException(status_code=400, detail="Select at least one source.")

    try:
        result = await orchestrator.execute_research(
            ResearchQueryRequest(
                query=req.message,
                chat_history=history[-MAX_HISTORY_MESSAGES:],
                search_sources=search_sources,
                document_ids=req.document_ids,
            )
        )
    except Exception as e:
        logger.exception("Chat failed")
        raise HTTPException(status_code=500, detail=f"Research synthesis error: {e}")

    SESSIONS[sid] = (history + [
        ChatMessage(role="user", content=req.message),
        ChatMessage(role="assistant", content=result.synthesized_answer),
    ])[-MAX_HISTORY_MESSAGES:]
    SESSIONS.move_to_end(sid)
    while len(SESSIONS) > MAX_SESSIONS:
        SESSIONS.popitem(last=False)

    return {
        "message_id": uuid.uuid4().hex,
        "answer": result.synthesized_answer,
        "evidence": [_evidence_to_api(e) for e in result.ranked_evidence],
    }


class ExportRequest(BaseModel):
    format: Literal["pdf", "docx", "md", "html", "bib"] = "pdf"
    title: str = "ARA Research Brief"
    content: str
    evidence: List[Dict[str, Any]] = Field(default_factory=list)


@app.post("/api/export", tags=["Export"])
async def export_answer(req: ExportRequest):
    if req.format == "bib":
        return PlainTextResponse(exporter.to_bibtex(req.evidence), media_type="application/x-bibtex")
    media_type, fn = exporter.EXPORTERS[req.format]
    try:
        body = await asyncio.to_thread(fn, req.title, req.content, req.evidence)
    except Exception:
        logger.exception("Export failed")
        raise HTTPException(status_code=500, detail="Export failed.")
    safe = re.sub(r"[^A-Za-z0-9_-]+", "-", req.title).strip("-")[:60] or "ara-brief"
    return Response(content=body, media_type=media_type,
                    headers={"Content-Disposition": f'attachment; filename="{safe}.{req.format}"'})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=settings.DEBUG)
