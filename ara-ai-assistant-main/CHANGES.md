# Fixes applied

Run backend (from repo root): `pip install -r backend/requirements.txt && uvicorn backend.main:app --reload`
Run tests: `pytest backend/tests -q`
Use real backend from the UI: set `VITE_USE_MOCK=false` in `frontend/.env`.

- Frontend/backend contract now matches `frontend/src/api/research.js` (`/api/chat`, `POST /api/documents`, 204 delete, PDF/DOCX export).
- No more fabricated synthesis: without an LLM you get a verbatim evidence digest.
- Uploads: PDF/TXT only, size limit, scanned/corrupt PDFs rejected (422), no raw-bytes fallback.
- Vector store wired in (embeds on upload, searches, deletes with the doc) when MONGODB_URI + OPENAI_API_KEY are set; otherwise keyword search.
- Blocking search SDK calls moved to threads. arXiv no longer marked peer-reviewed.
- Export escapes HTML. CORS: explicit origins only (set CORS_ORIGINS in .env).
- Scoring matches whole words. Misc crash/deprecation fixes.
- Repo: removed nested duplicate project + node_modules dump; Express files moved to `legacy-express/`.
