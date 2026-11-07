"""
Document Ingestion & Chunking Service for ARA.
PyPDF extraction -> LangChain RecursiveCharacterTextSplitter -> in-memory store
(+ MongoDB vector store when configured).
"""

import io
import re
import uuid
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from langchain_text_splitters import RecursiveCharacterTextSplitter
from backend.schemas import IndexedDocument, DocumentChunk
from backend.config import settings
from backend.services.vector_store import vector_store

logger = logging.getLogger(__name__)

# In-memory registry of uploaded documents (source of truth for what is "active")
DOCUMENT_STORE: Dict[str, IndexedDocument] = {}

SUPPORTED_TYPES = ("pdf", "txt")


class DocumentError(ValueError):
    """Raised when a document cannot be ingested (user-facing message)."""


def _tokens(text: str) -> List[str]:
    """Lowercase word tokens (>2 chars) with a crude plural strip."""
    out = []
    for w in re.findall(r"[a-z0-9]+", text.lower()):
        if len(w) > 2:
            out.append(w[:-1] if len(w) > 3 and w.endswith("s") else w)
    return out


class DocumentLoaderService:
    def __init__(self):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", ". ", " ", ""],
        )

    def extract_text_from_pdf(self, file_bytes: bytes) -> str:
        try:
            import pypdf
            reader = pypdf.PdfReader(io.BytesIO(file_bytes))
            parts = [(page.extract_text() or "") for page in reader.pages]
        except Exception as e:
            logger.error(f"Failed to parse PDF with pypdf: {e}")
            raise DocumentError("Could not read this PDF. The file may be corrupted or encrypted.")
        return "\n\n".join(p for p in parts if p.strip())

    def process_and_index_document(self, filename: str, file_bytes: bytes, file_type: str = "pdf") -> IndexedDocument:
        """Extracts text, chunks it and indexes the chunks. Raises DocumentError on bad input."""
        if file_type not in SUPPORTED_TYPES:
            raise DocumentError(f"Unsupported file type '{file_type}'. Upload a PDF or TXT file.")
        if not file_bytes:
            raise DocumentError("The uploaded file is empty.")
        if len(file_bytes) > settings.MAX_UPLOAD_MB * 1024 * 1024:
            raise DocumentError(f"File is larger than the {settings.MAX_UPLOAD_MB} MB limit.")

        raw_text = (
            self.extract_text_from_pdf(file_bytes)
            if file_type == "pdf"
            else file_bytes.decode("utf-8", errors="ignore")
        )
        if not raw_text.strip():
            raise DocumentError(
                "No extractable text found. Scanned/image-only PDFs are not supported yet."
            )

        doc_id = f"doc_{uuid.uuid4().hex[:8]}"
        chunks: List[DocumentChunk] = [
            DocumentChunk(
                chunk_id=f"{doc_id}-chk-{idx}",
                doc_id=doc_id,
                chunk_index=idx,
                text=text,
                char_count=len(text),
                token_estimate=max(1, len(text) // 4),
            )
            for idx, text in enumerate(self.text_splitter.split_text(raw_text))
        ]

        doc = IndexedDocument(
            id=doc_id,
            name=filename,
            file_type=file_type,
            size_bytes=len(file_bytes),
            uploaded_at=datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            chunk_count=len(chunks),
            total_words=len(raw_text.split()),
            status="ready",
            chunks=chunks,
        )
        DOCUMENT_STORE[doc_id] = doc

        # Embed + store for vector search (no-op when Mongo/OpenAI are not configured)
        vector_store.add_chunks(
            texts=[c.text for c in chunks],
            metadatas=[
                {"doc_id": doc_id, "chunk_id": c.chunk_id, "chunk_index": c.chunk_index, "filename": filename}
                for c in chunks
            ],
        )
        return doc

    def delete_document(self, doc_id: str) -> bool:
        if doc_id not in DOCUMENT_STORE:
            return False
        del DOCUMENT_STORE[doc_id]
        vector_store.delete_document(doc_id)
        return True

    @staticmethod
    def _candidate(doc: IndexedDocument, chunk_id: str, chunk_index: int, text: str, score: float) -> Dict[str, Any]:
        return {
            "id": chunk_id,
            "title": f"Uploaded Reference: {doc.name}",
            "authors": ["User Upload"],
            "url": f"document://{doc.id}/{chunk_index}",
            "snippet": text,
            "source_type": "uploaded_doc",
            "journal_or_domain": doc.name,
            "is_peer_reviewed": False,
            "chunk_id": chunk_id,
            "_match_score": score,
        }

    def search_chunks_by_query(
        self, query: str, document_ids: Optional[List[str]] = None, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """Vector search when available, otherwise keyword overlap. Blocking."""
        target_docs = (
            [DOCUMENT_STORE[d] for d in document_ids if d in DOCUMENT_STORE]
            if document_ids
            else list(DOCUMENT_STORE.values())
        )
        if not target_docs:
            return []
        by_id = {d.id: d for d in target_docs}

        if vector_store.is_connected():
            hits = vector_store.similarity_search(query, k=top_k, doc_ids=list(by_id))
            candidates = []
            for h in hits:
                m = h["metadata"]
                doc = by_id.get(m.get("doc_id"))
                if doc:
                    candidates.append(
                        self._candidate(doc, m.get("chunk_id", ""), m.get("chunk_index", 0), h["text"], h["score"])
                    )
            if candidates:
                return candidates

        query_terms = set(_tokens(query))
        candidates = []
        for doc in target_docs:
            for chunk in doc.chunks or []:
                overlap = len(query_terms & set(_tokens(chunk.text)))
                if overlap:
                    candidates.append(self._candidate(doc, chunk.chunk_id, chunk.chunk_index, chunk.text, overlap))
        candidates.sort(key=lambda x: x["_match_score"], reverse=True)
        return candidates[:top_k]
