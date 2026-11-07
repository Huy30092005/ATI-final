"""
Automated Scoring & Quality Control Engine for ARA.
Evaluates gathered information based on academic credibility, lexical/semantic relevance,
and contextual coherence, discarding low-quality or irrelevant data.
"""

import re
from typing import List, Tuple, Dict, Any, Optional
from urllib.parse import urlparse
from backend.schemas import SourceEvidence, QualityMetrics

HIGH_AUTHORITY_DOMAINS: Dict[str, float] = {
    "arxiv.org": 0.95,
    "nature.com": 0.99,
    "science.org": 0.99,
    "cell.com": 0.98,
    "thelancet.com": 0.98,
    "sciencedirect.com": 0.94,
    "ieee.org": 0.95,
    "acm.org": 0.95,
    "nih.gov": 0.98,
    "ncbi.nlm.nih.gov": 0.98,
    "pubmed.ncbi.nlm.nih.gov": 0.98,
    "semanticscholar.org": 0.92,
    "crossref.org": 0.90,
    "springer.com": 0.93,
    "wiley.com": 0.92,
    "oup.com": 0.94,
    "cambridge.org": 0.94,
    "mit.edu": 0.96,
    "stanford.edu": 0.96,
    "harvard.edu": 0.96,
}


def evaluate_domain_credibility(domain_or_url: str) -> float:
    """Computes base credibility from domain authority."""
    if not domain_or_url:
        return 0.50

    try:
        if "://" in domain_or_url:
            host = urlparse(domain_or_url).netloc.lower()
        else:
            host = domain_or_url.lower().split("/")[0]
        if host.startswith("www."):
            host = host[4:]
    except Exception:
        host = domain_or_url.lower()

    for domain, score in HIGH_AUTHORITY_DOMAINS.items():
        if host == domain or host.endswith(f".{domain}"):
            return score

    if host.endswith(".edu"):
        return 0.90
    if host.endswith(".gov"):
        return 0.92
    if host.endswith(".org"):
        return 0.78
    if host.endswith(".io") or host.endswith(".com"):
        return 0.65
    return 0.55


def calculate_credibility_score(
    source_type: str,
    journal_or_domain: str,
    authors: Optional[List[str]] = None,
    is_peer_reviewed: bool = False,
    citation_count: Optional[int] = None,
    published_year: Optional[int] = None,
) -> float:
    """Calculates composite academic credibility (0.0 to 1.0)."""
    if source_type == "uploaded_doc":
        base_score = 0.92  # Direct user grounding document
    elif source_type == "academic_db":
        base_score = 0.90  # Peer reviewed / verified repo
    else:
        base_score = evaluate_domain_credibility(journal_or_domain)

    if authors and len(authors) > 0:
        base_score += 0.04

    if is_peer_reviewed:
        base_score += 0.05

    if citation_count and citation_count > 50:
        base_score += 0.03

    if published_year:
        age = max(0, 2026 - published_year)
        if age <= 3:
            base_score += 0.03
        elif age > 20:
            base_score -= 0.02

    return min(0.99, max(0.10, round(base_score, 2)))


def calculate_relevance_score(query: str, snippet: str, title: str = "") -> float:
    """Calculates term frequency and title match relevance."""
    if not query or (not snippet and not title):
        return 0.0

    def tokenize(text: str) -> List[str]:
        # whole words only, with a crude plural strip ("models" ~ "model")
        words = re.findall(r"\b[a-zA-Z0-9]{3,}\b", text.lower())
        return [w[:-1] if len(w) > 3 and w.endswith("s") else w for w in words]

    query_tokens = tokenize(query)
    if not query_tokens:
        return 0.5

    content_tokens = tokenize(snippet)
    title_tokens = tokenize(title)

    match_score = 0.0
    for term in query_tokens:
        in_title = sum(1 for t in title_tokens if term == t)
        in_content = sum(1 for t in content_tokens if term == t)

        if in_title > 0:
            match_score += 0.40
        if in_content > 0:
            match_score += 0.35 + min(0.25, in_content * 0.05)

    matched_count = sum(
        1 for term in query_tokens
        if term in title_tokens or term in content_tokens
    )
    fraction_matched = matched_count / len(query_tokens)
    raw = fraction_matched * 0.65 + (min(1.0, match_score / (len(query_tokens) * 0.5)) * 0.35)

    return min(0.99, max(0.10, round(raw, 2)))


class ScoringEngine:
    def __init__(self, min_credibility: float = 0.60):
        self.min_credibility = min_credibility

    def evaluate_and_rank(
        self,
        raw_candidates: List[Dict[str, Any]],
        query: str,
        min_credibility_override: Optional[float] = None,
    ) -> Tuple[List[SourceEvidence], List[SourceEvidence], QualityMetrics]:
        """
        Runs quality control, scores each candidate, filters low-credibility items,
        and produces ranked evidence with full metrics.
        """
        threshold = min_credibility_override if min_credibility_override is not None else self.min_credibility

        evaluated: List[SourceEvidence] = []
        for c in raw_candidates:
            cred = calculate_credibility_score(
                source_type=c.get("source_type", "live_web"),
                journal_or_domain=c.get("journal_or_domain", ""),
                authors=c.get("authors", []),
                is_peer_reviewed=c.get("is_peer_reviewed", False),
                citation_count=c.get("citation_count"),
                published_year=c.get("published_year"),
            )
            rel = calculate_relevance_score(
                query=query,
                snippet=c.get("snippet", ""),
                title=c.get("title", ""),
            )
            # Composite formula: 55% relevance, 45% credibility
            composite = round(rel * 0.55 + cred * 0.45, 3)

            evaluated.append(
                SourceEvidence(
                    id=c.get("id", f"src-{len(evaluated)+1}"),
                    title=c.get("title", "Untitled Reference"),
                    authors=c.get("authors", []),
                    url=c.get("url", ""),
                    snippet=c.get("snippet", ""),
                    source_type=c.get("source_type", "live_web"),
                    published_year=c.get("published_year"),
                    journal_or_domain=c.get("journal_or_domain", "Web"),
                    credibility_score=cred,
                    relevance_score=rel,
                    composite_rank=composite,
                    is_peer_reviewed=c.get("is_peer_reviewed", False),
                    citation_count=c.get("citation_count"),
                    doi=c.get("doi"),
                    chunk_id=c.get("chunk_id"),
                )
            )

        # Sort descending by composite rank
        evaluated.sort(key=lambda x: x.composite_rank, reverse=True)

        ranked: List[SourceEvidence] = []
        discarded: List[SourceEvidence] = []

        for item in evaluated:
            if item.credibility_score >= threshold and item.relevance_score >= 0.20:
                ranked.append(item)
            else:
                discarded.append(item)

        total_evaluated = len(evaluated)
        avg_cred = (
            round(sum(x.credibility_score for x in evaluated) / total_evaluated, 2)
            if total_evaluated > 0
            else 0.0
        )
        avg_rel = (
            round(sum(x.relevance_score for x in evaluated) / total_evaluated, 2)
            if total_evaluated > 0
            else 0.0
        )

        metrics = QualityMetrics(
            total_retrieved=len(raw_candidates),
            evaluated_count=total_evaluated,
            discarded_count=len(discarded),
            top_ranked_count=len(ranked),
            average_credibility=avg_cred,
            average_relevance=avg_rel,
        )

        return ranked, discarded, metrics
