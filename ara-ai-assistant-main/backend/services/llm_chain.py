"""
LangChain LLM Synthesis Chain with OpenAI for ARA.
Synthesizes verified, ranked multi-source evidence into a structured research brief
with inline citations [1], [2], methodological critique, and counter-evidence.
"""

import logging
import json
from typing import List, Dict, Any, Optional

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI

from backend.schemas import SourceEvidence, AcademicDepth
from backend.config import settings

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are ARA (AI Research Assistant), an elite academic synthesis engine.
Your purpose is to assist researchers in finding evidence, validating references, and synthesizing multiple sources into a single, well-structured research document.

CRITICAL CITATION RULES:
1. Ground your analysis strictly in the provided Ranked Evidence.
2. Every major claim, statistic, or finding MUST include an inline bracketed citation, e.g., [1], [2], or [1, 3], matching the exact indices in the Evidence list.
3. If an evidence item has conflicting conclusions or methodological caveats, state them explicitly.
4. Do NOT fabricate citations or reference numbers that do not exist in the evidence.

STRUCTURE YOUR OUTPUT WITH THESE EXACT SECTIONS:
## Executive Summary
(1-2 paragraphs synthesizing the core state of knowledge with citations)

## Key Findings & Empirical Evidence
(Bulleted points highlighting verified findings with [1], [2] citations)

## Methodology & Evidence Quality Review
(Critical evaluation of study designs, sample sizes, and data credibility)

## Counter-Evidence & Limitations
(Alternative perspectives, confounding variables, or disputed findings)

## Suggested Next Research Directions
(3 specific follow-up questions to investigate further)
"""


class LLMChainService:
    def __init__(self):
        self.api_key = settings.OPENAI_API_KEY
        self.model_name = settings.OPENAI_MODEL

    def is_available(self) -> bool:
        return bool(self.api_key and len(self.api_key) > 10)

    def format_evidence_context(self, evidence_list: List[SourceEvidence]) -> str:
        """Formats evidence into indexed context blocks for the LLM."""
        formatted_blocks = []
        for idx, item in enumerate(evidence_list, 1):
            authors_str = ", ".join(item.authors) if item.authors else "Unknown"
            year_str = str(item.published_year) if item.published_year else "n.d."
            peer_str = " (Peer-Reviewed)" if item.is_peer_reviewed else ""

            block = f"""[{idx}] {item.title}
Authors: {authors_str} ({year_str}) | Source: {item.journal_or_domain}{peer_str}
Credibility: {int(item.credibility_score * 100)}% | Relevance: {int(item.relevance_score * 100)}% | Type: {item.source_type}
Excerpt: {item.snippet}"""
            formatted_blocks.append(block)

        return "\n\n".join(formatted_blocks)

    async def generate_synthesis(
        self,
        query: str,
        ranked_evidence: List[SourceEvidence],
        academic_depth: AcademicDepth = "peer_review",
        include_counterarguments: bool = True,
        chat_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """Runs LangChain prompt pipeline over curated evidence bundle."""
        if not ranked_evidence:
            return {
                "synthesized_answer": "No credible evidence met the quality threshold for this query. Consider lowering the minimum credibility threshold or expanding search sources.",
                "key_findings": ["No verified evidence available."],
                "methodology_critique": "Insufficient data to perform methodology evaluation.",
                "counterarguments": None,
                "suggested_followups": ["Refine query keywords", "Include broader live web domains"],
            }

        evidence_context = self.format_evidence_context(ranked_evidence)

        depth_instructions = {
            "undergraduate": "Provide clear, accessible explanations with foundational context while maintaining citation rigor.",
            "peer_review": "Use rigorous technical terminology, critique statistical validity, and detail exact mechanisms.",
            "systematic_review": "Adopt PRISMA-style synthesis depth, contrasting effect sizes, biases, and consensus degrees.",
        }.get(academic_depth, "Use rigorous technical depth.")

        user_content = f"""Research Query: {query}
Academic Depth: {academic_depth.upper()} ({depth_instructions})
Counterarguments Requested: {'Yes' if include_counterarguments else 'No'}

=== RANKED EVIDENCE BUNDLE ===
{evidence_context}
==============================

Synthesize the research brief following the required structure."""

        # If OpenAI API is available, invoke LangChain ChatOpenAI
        if self.is_available():
            try:
                llm = ChatOpenAI(
                    model=self.model_name,
                    api_key=self.api_key,
                    temperature=0.2,
                )

                prompt = ChatPromptTemplate.from_messages([
                    ("system", SYSTEM_PROMPT),
                    ("user", "{input_text}"),
                ])

                chain = prompt | llm | StrOutputParser()
                output_text = await chain.ainvoke({"input_text": user_content})

                # Extract key findings bullets
                findings = []
                for line in output_text.split("\n"):
                    line_clean = line.strip()
                    if (line_clean.startswith("- ") or line_clean.startswith("* ")) and len(line_clean) > 20:
                        findings.append(line_clean.lstrip("-* ").strip())
                    if len(findings) >= 5:
                        break

                return {
                    "synthesized_answer": output_text,
                    "key_findings": findings,
                    "methodology_critique": None,
                    "counterarguments": None,
                    "suggested_followups": [
                        f"What are the longitudinal outcomes related to {query[:30]}?",
                        f"How do recent preprints compare with earlier landmark studies on {query[:30]}?",
                        "What are the main practical challenges in applying these findings?",
                    ],
                }
            except Exception as e:
                logger.error(f"OpenAI LangChain execution failed: {e}")

        # No LLM available: show the retrieved evidence honestly instead of inventing findings
        return self._evidence_digest(query, ranked_evidence)

    def _evidence_digest(self, query: str, ranked_evidence: List[SourceEvidence]) -> Dict[str, Any]:
        """LLM-free fallback: lists the retrieved excerpts verbatim. Never makes claims of its own."""
        lines = [
            "## Evidence Digest (AI synthesis unavailable)",
            f"The language model could not be reached, so no synthesis was generated for **{query}**. "
            "These are the highest-ranked sources that were retrieved:",
            "",
        ]
        for idx, item in enumerate(ranked_evidence[:6], 1):
            snippet = item.snippet.strip().replace("\n", " ")
            lines.append(f"- **[{idx}] {item.title}** ({item.journal_or_domain}): {snippet[:300]}")
        return {
            "synthesized_answer": "\n".join(lines),
            "key_findings": [],
            "methodology_critique": None,
            "counterarguments": None,
            "suggested_followups": [],
        }
