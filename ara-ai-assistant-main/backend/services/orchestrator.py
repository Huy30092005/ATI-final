"""
ARA Master Orchestrator.
Coordinates the entire multi-source research pipeline:
1. Multi-source evidence gathering (Uploaded docs, live web, academic DBs)
2. Automated Quality Control & Credibility Ranking
3. Contextual synthesis bundling
4. LangChain LLM answer generation with inline citations
"""

import time
import asyncio
import logging
from typing import List, Dict, Any, Optional

from backend.schemas import (
    ResearchQueryRequest,
    ResearchQueryResponse,
    PipelineStep,
    SourceEvidence,
)
from backend.services.search_service import SearchService
from backend.services.document_loader import DocumentLoaderService
from backend.services.scoring_engine import ScoringEngine
from backend.services.llm_chain import LLMChainService

logger = logging.getLogger(__name__)


class ResearchOrchestrator:
    def __init__(self):
        self.search_service = SearchService()
        self.doc_service = DocumentLoaderService()
        self.scoring_engine = ScoringEngine()
        self.llm_service = LLMChainService()

    async def execute_research(self, request: ResearchQueryRequest) -> ResearchQueryResponse:
        start_time = time.time()
        pipeline_trace: List[PipelineStep] = []

        # --- STEP 1: Multi-Source Gathering ---
        step1_start = time.time()
        pipeline_trace.append(PipelineStep(
            id="step-1",
            title="Multi-Source Knowledge Gathering",
            description="Concurrently querying uploaded documents, live internet, and academic databases",
            status="running"
        ))

        tasks = []
        sources_to_query = request.search_sources or ["uploaded_docs", "live_web", "academic_db"]

        # 1. Uploaded Documents
        if "uploaded_docs" in sources_to_query:
            tasks.append(
                asyncio.to_thread(
                    self.doc_service.search_chunks_by_query,
                    request.query,
                    request.document_ids,
                    5
                )
            )
        else:
            tasks.append(asyncio.sleep(0, result=[]))

        # 2. Live Internet Search
        if "live_web" in sources_to_query:
            tasks.append(self.search_service.search_live_web(request.query, max_results=6))
        else:
            tasks.append(asyncio.sleep(0, result=[]))

        # 3. Verified Academic DBs (arXiv + Semantic Scholar)
        if "academic_db" in sources_to_query:
            tasks.append(self.search_service.search_academic_arxiv(request.query, max_results=4))
            tasks.append(self.search_service.search_academic_semanticscholar(request.query, max_results=4))
        else:
            tasks.append(asyncio.sleep(0, result=[]))
            tasks.append(asyncio.sleep(0, result=[]))

        gathered_results = await asyncio.gather(*tasks, return_exceptions=True)

        raw_candidates: List[Dict[str, Any]] = []
        for res in gathered_results:
            if isinstance(res, list):
                raw_candidates.extend(res)

        step1_duration = int((time.time() - step1_start) * 1000)
        pipeline_trace[0].status = "completed"
        pipeline_trace[0].duration_ms = step1_duration
        pipeline_trace[0].details = f"Retrieved {len(raw_candidates)} candidate references across selected channels."

        # --- STEP 2: Automated Scoring & Quality Control ---
        step2_start = time.time()
        step2 = PipelineStep(
            id="step-2",
            title="Quality Control & Evidence Ranking",
            description="Scoring academic credibility, BM25/semantic relevance, and discarding low-trust sources",
            status="running"
        )
        pipeline_trace.append(step2)

        min_cred = request.min_credibility if request.min_credibility is not None else 0.60
        ranked_evidence, discarded_evidence, quality_metrics = self.scoring_engine.evaluate_and_rank(
            raw_candidates=raw_candidates,
            query=request.query,
            min_credibility_override=min_cred,
        )

        step2_duration = int((time.time() - step2_start) * 1000)
        step2.status = "completed"
        step2.duration_ms = step2_duration
        step2.details = (
            f"Validated {len(ranked_evidence)} high-fidelity sources (Avg Credibility: "
            f"{int(quality_metrics.average_credibility * 100)}%). Discarded {len(discarded_evidence)} items below threshold."
        )

        # --- STEP 3: Contextual Synthesis & LLM Generation ---
        step3_start = time.time()
        step3 = PipelineStep(
            id="step-3",
            title="Contextual Synthesis & Citation Grounding",
            description="Synthesizing multi-source evidence bundle with LangChain and OpenAI",
            status="running"
        )
        pipeline_trace.append(step3)

        synthesis_result = await self.llm_service.generate_synthesis(
            query=request.query,
            ranked_evidence=ranked_evidence,
            academic_depth=request.academic_depth or "peer_review",
            include_counterarguments=request.include_counterarguments if request.include_counterarguments is not None else True,
            chat_history=[m.model_dump() for m in request.chat_history] if request.chat_history else None,
        )

        step3_duration = int((time.time() - step3_start) * 1000)
        step3.status = "completed"
        step3.duration_ms = step3_duration
        step3.details = f"Synthesized research brief with {len(synthesis_result.get('key_findings', []))} key findings and inline citations."

        total_execution_ms = int((time.time() - start_time) * 1000)

        return ResearchQueryResponse(
            query=request.query,
            synthesized_answer=synthesis_result["synthesized_answer"],
            key_findings=synthesis_result.get("key_findings", []),
            methodology_critique=synthesis_result.get("methodology_critique"),
            counterarguments=synthesis_result.get("counterarguments"),
            ranked_evidence=ranked_evidence,
            discarded_evidence=discarded_evidence,
            quality_metrics=quality_metrics,
            pipeline_trace=pipeline_trace,
            suggested_followups=synthesis_result.get("suggested_followups", []),
            execution_time_ms=total_execution_ms,
        )
