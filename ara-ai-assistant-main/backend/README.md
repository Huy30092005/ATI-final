# ARA (AI Research Assistant) - Backend

ARA is an autonomous AI-powered application created to assist researchers in finding evidence, validating references, and synthesizing multiple sources into a single, well-structured document.

This `/backend` folder contains the complete, production-ready backend implementations for ARA:
1. **Python / FastAPI / LangChain Stack**: Production backend utilizing LangChain for orchestration, FastAPI for high-performance API endpoints, OpenAI (`gpt-4o`) for natural language research synthesis, and live academic search capabilities.
2. **Node.js / Express Full-Stack Server**: Modular server routes running Vite in development and providing instant out-of-the-box local testing.

---

## Directory Structure

```
/backend
├── __init__.py                # Python package root
├── main.py                    # FastAPI application entry point with CORS and REST routes
├── config.py                  # Pydantic Settings (OpenAI, MongoDB, Tavily/Search, Port)
├── schemas.py                 # Pydantic models (ResearchQuery, SourceEvidence, Metrics)
├── requirements.txt           # Pinned Python dependencies
├── Dockerfile                 # Container image definition for deployment
├── README.md                  # Complete documentation and setup guide
├── services/                  # LangChain & AI pipeline services
│   ├── __init__.py
│   ├── orchestrator.py        # Master research coordinator
│   ├── scoring_engine.py      # Automated credibility scoring & ranking algorithm
│   ├── search_service.py      # Multi-source search (arXiv, Semantic Scholar, DuckDuckGo)
│   ├── document_loader.py     # PDF text extraction & LangChain RecursiveCharacterTextSplitter
│   ├── llm_chain.py           # LangChain OpenAI prompt templates and synthesis chain
│   └── vector_store.py        # MongoDB Atlas Vector Search integration
├── routes/                    # Modular Express routes
│   ├── health.ts              # /api/health
│   ├── documents.ts           # /api/documents & /api/documents/upload
│   ├── research.ts            # /api/research/query
│   └── export.ts              # /api/export
└── server.ts                  # Express full-stack entry point
```

---

## Architecture & Data Flow

1. **User Input & Document Ingestion (`POST /api/documents/upload`)**:
   - Accepts uploaded PDF and text reference papers.
   - Parses text using `pypdf`.
   - Chunks text into searchable context blocks using LangChain's `RecursiveCharacterTextSplitter(chunk_size=800, chunk_overlap=150)`.
   - Embeds and indexes chunks in MongoDB Atlas Vector Search (or in-memory vector store).

2. **Multi-Source Knowledge Gathering (`POST /api/research/query`)**:
   - Simultaneously searches three distinct knowledge bases:
     - **Uploaded Reference Documents**: Vector & lexical chunk match.
     - **Live Internet Data**: DuckDuckGo search / Tavily API.
     - **Verified Academic Databases**: arXiv API & Semantic Scholar Graph API.

3. **Quality Control & Automated Scoring Engine**:
   - Evaluates each piece of gathered information:
     - **Academic Credibility Score**: Domain authority (.edu, .gov, peer-reviewed journals), author attribution, publication recency.
     - **Relevance Score**: Query token frequency, title match, and semantic alignment.
     - **Composite Rank**: Weighted balance (55% relevance, 45% credibility).
   - Automatically **discards** low-credibility (below threshold) and irrelevant sources.

4. **Contextual Synthesis & LangChain LLM Generation**:
   - Bundles the research question, conversation history, and curated evidence.
   - Prompts OpenAI (`gpt-4o`) via LangChain to generate a structured synthesis with verified bracketed inline citations `[1]`, `[2]`, methodology critique, counterarguments, and export-ready references.

5. **Delivery & Export (`POST /api/export`)**:
   - Clean markdown, formatted HTML/PDF, and BibTeX citations.

---

## Running the Python FastAPI Backend

### 1. Installation

```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure Environment Variables (`.env`)

Create a `.env` file in the root or `backend/` directory:

```env
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-4o

# Optional: MongoDB Atlas Vector Search
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=ara_research_db
MONGODB_COLLECTION=document_embeddings

# Optional: Enhanced Web Search
TAVILY_API_KEY=tvly-your-tavily-key
```

### 3. Run the FastAPI Server

```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

* **Interactive Swagger UI**: `http://localhost:8000/docs`
* **OpenAPI Schema**: `http://localhost:8000/openapi.json`

---

## Pushing to your GitHub Repository

To commit this `backend/` directory into your repository `https://github.com/datk23hanu/ara-ai-assistant.git`:

```bash
git add backend/
git commit -m "feat(backend): modularize Python FastAPI, LangChain & Express research services into backend folder"
git push origin main
```
