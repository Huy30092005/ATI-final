"""
Pydantic schemas and Data Transfer Objects for ARA (AI Research Assistant).
Fully aligned with the React frontend interfaces.
"""

from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field


SourceType = Literal["uploaded_doc", "academic_db", "live_web"]
AcademicDepth = Literal["undergraduate", "peer_review", "systematic_review"]


class SourceEvidence(BaseModel):
    id: str = Field(..., description="Unique ID of the evidence item")
    title: str = Field(..., description="Title of the paper or article")
    authors: List[str] = Field(default_factory=list, description="List of author names")
    url: str = Field(..., description="Canonical URL or DOI link")
    snippet: str = Field(..., description="Extracted content excerpt relevant to the query")
    source_type: SourceType = Field(..., description="Knowledge base origin")
    published_year: Optional[int] = Field(None, description="Year of publication")
    journal_or_domain: str = Field(..., description="Journal name, repository or website domain")
    credibility_score: float = Field(..., description="Automated credibility score (0.0 - 1.0)")
    relevance_score: float = Field(..., description="BM25/semantic relevance score (0.0 - 1.0)")
    composite_rank: float = Field(..., description="Weighted quality score used for ranking")
    is_peer_reviewed: Optional[bool] = Field(False, description="Whether from peer-reviewed source")
    citation_count: Optional[int] = Field(None, description="Estimated academic citation count")
    doi: Optional[str] = Field(None, description="Digital Object Identifier if available")
    chunk_id: Optional[str] = Field(None, description="Underlying document chunk ID if from upload")


class QualityMetrics(BaseModel):
    total_retrieved: int = Field(..., description="Total raw sources pulled across all 3 channels")
    evaluated_count: int = Field(..., description="Count of sources analyzed by the scoring engine")
    discarded_count: int = Field(..., description="Count of low-credibility or irrelevant items discarded")
    top_ranked_count: int = Field(..., description="Count of validated evidence items used in LLM synthesis")
    average_credibility: float = Field(..., description="Mean credibility of accepted evidence")
    average_relevance: float = Field(..., description="Mean relevance score")


class PipelineStep(BaseModel):
    id: str
    title: str
    description: str
    status: Literal["pending", "running", "completed", "failed"] = "pending"
    details: Optional[str] = None
    duration_ms: Optional[int] = None


class ChatMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ResearchQueryRequest(BaseModel):
    query: str = Field(..., min_length=3, description="The research question or topic prompt")
    chat_history: Optional[List[ChatMessage]] = Field(default_factory=list)
    search_sources: Optional[List[str]] = Field(
        default=["uploaded_docs", "live_web", "academic_db"],
        description="Knowledge bases to query simultaneously"
    )
    academic_depth: Optional[AcademicDepth] = Field("peer_review")
    min_credibility: Optional[float] = Field(0.60, ge=0.0, le=1.0)
    include_counterarguments: Optional[bool] = Field(True)
    document_ids: Optional[List[str]] = Field(default_factory=list)


class ResearchQueryResponse(BaseModel):
    query: str
    synthesized_answer: str = Field(..., description="Comprehensive answer with inline citations [1], [2]")
    key_findings: List[str] = Field(default_factory=list, description="Bulleted takeaway discoveries")
    methodology_critique: Optional[str] = Field(None, description="Critique of methodologies across studies")
    counterarguments: Optional[str] = Field(None, description="Identified counter-evidence or contradictions")
    ranked_evidence: List[SourceEvidence] = Field(default_factory=list)
    discarded_evidence: Optional[List[SourceEvidence]] = Field(default_factory=list)
    quality_metrics: QualityMetrics
    pipeline_trace: List[PipelineStep]
    suggested_followups: List[str] = Field(default_factory=list)
    execution_time_ms: int


class DocumentChunk(BaseModel):
    chunk_id: str
    doc_id: str
    chunk_index: int
    text: str
    char_count: int
    token_estimate: int


class IndexedDocument(BaseModel):
    id: str
    name: str
    file_type: Literal["pdf", "txt"]
    size_bytes: int
    uploaded_at: str
    chunk_count: int
    total_words: int
    status: Literal["ready", "indexing", "failed"]
    chunks: Optional[List[DocumentChunk]] = None


class DocumentUploadResponse(BaseModel):
    message: str
    document: IndexedDocument


class ApiHealthResponse(BaseModel):
    status: str
    backend_engine: str = "fastapi_python"
    openai_configured: bool
    mongodb_configured: bool
    search_provider: str
    version: str = "1.0.0"
