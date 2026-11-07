"""Run from the repo root:  pytest backend/tests -q   (no network / API keys needed)"""
import io
import pytest
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas

from backend.main import app
from backend.services.search_service import SearchService
from backend.services.scoring_engine import calculate_relevance_score


@pytest.fixture()
def client(monkeypatch):
    async def no_web(self, *a, **k):
        return []
    monkeypatch.setattr(SearchService, "search_live_web", no_web)
    monkeypatch.setattr(SearchService, "search_academic_arxiv", no_web)
    monkeypatch.setattr(SearchService, "search_academic_semanticscholar", no_web)
    monkeypatch.setattr("backend.config.settings.OPENAI_API_KEY", None)
    with TestClient(app) as c:
        yield c


def make_pdf(text):
    buf = io.BytesIO()
    c = canvas.Canvas(buf)
    if text:
        c.drawString(72, 700, text)
    c.showPage(); c.save()
    return buf.getvalue()


def test_upload_pdf_list_delete(client):
    r = client.post("/api/documents", files={"file": ("a.pdf", make_pdf("Transformers use self attention"), "application/pdf")})
    assert r.status_code == 200
    doc = r.json()
    assert set(doc) == {"id", "name", "size", "status", "chunks"} and doc["status"] == "ready"
    assert doc["id"] in [d["id"] for d in client.get("/api/documents").json()]
    assert client.delete(f"/api/documents/{doc['id']}").status_code == 204
    assert client.delete(f"/api/documents/{doc['id']}").status_code == 404


def test_scanned_pdf_rejected(client):
    r = client.post("/api/documents", files={"file": ("scan.pdf", make_pdf(None), "application/pdf")})
    assert r.status_code == 422 and "Scanned" in r.json()["detail"]


def test_corrupt_pdf_not_decoded_as_text(client):
    r = client.post("/api/documents", files={"file": ("bad.pdf", b"this is not a pdf", "application/pdf")})
    assert r.status_code == 422


def test_unsupported_and_oversized(client, monkeypatch):
    assert client.post("/api/documents", files={"file": ("a.docx", b"x", "application/octet-stream")}).status_code == 415
    monkeypatch.setattr("backend.config.settings.MAX_UPLOAD_MB", 0)
    assert client.post("/api/documents", files={"file": ("a.txt", b"hello world text", "text/plain")}).status_code == 413


def test_chat_uses_uploaded_doc_and_never_fabricates(client):
    doc = client.post("/api/documents", files={"file": ("n.txt", b"Gradient descent minimizes loss by following the negative gradient.", "text/plain")}).json()
    r = client.post("/api/chat", json={"session_id": "s1", "message": "How does gradient descent work?",
                                       "document_ids": [doc["id"]], "sources": {"documents": True, "web": False, "academic": False}})
    assert r.status_code == 200
    body = r.json()
    assert body["evidence"][0]["source_type"] == "document" and body["evidence"][0]["url"] is None
    assert "unavailable" in body["answer"] and "88%" not in body["answer"]
    assert "negative gradient" in body["answer"]  # real retrieved text only


def test_chat_requires_a_source(client):
    r = client.post("/api/chat", json={"message": "hello there", "sources": {"documents": False, "web": False, "academic": False}})
    assert r.status_code == 400


def test_export_html_escapes_and_binary_formats(client):
    evil = "<script>alert(1)</script>"
    payload = {"title": evil, "content": evil, "evidence": [{"title": evil, "authors": [evil], "year": 2024, "url": "http://x"}]}
    html = client.post("/api/export", json={**payload, "format": "html"})
    assert "<script>alert" not in html.text
    assert client.post("/api/export", json={**payload, "format": "pdf"}).content[:4] == b"%PDF"
    assert client.post("/api/export", json={**payload, "format": "docx"}).content[:2] == b"PK"
    assert "@misc" in client.post("/api/export", json={**payload, "format": "bib"}).text


def test_relevance_uses_whole_words():
    assert calculate_relevance_score("ai safety", "maintain the main chain", "") < 0.2
    assert calculate_relevance_score("language models", "A language model is trained", "") > 0.5


def test_health_and_cors(client):
    assert client.get("/api/health").json()["status"] == "healthy"
    r = client.options("/api/chat", headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "POST"})
    assert "access-control-allow-origin" not in r.headers
