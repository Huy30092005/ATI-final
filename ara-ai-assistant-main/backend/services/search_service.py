"""
Multi-source Search Service for ARA.
Pulls evidence concurrently from:
1. Verified Academic Databases (arXiv API, Semantic Scholar)
2. Live Internet Web Search (DuckDuckGo Search, Tavily, SerpAPI)
"""

import asyncio
import logging
from typing import List, Dict, Any, Optional
import httpx
from backend.config import settings

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self):
        self.tavily_key = settings.TAVILY_API_KEY
        self.serpapi_key = settings.SERPAPI_API_KEY

    async def search_academic_arxiv(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Queries arXiv API for pre-prints and peer-grade physics/CS/bio papers."""
        results = []
        try:
            url = "https://export.arxiv.org/api/query"
            params = {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "relevance",
                "sortOrder": "descending",
            }
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(resp.text)
                    ns = {"atom": "http://www.w3.org/2005/Atom", "arxiv": "http://arxiv.org/schemas/atom"}

                    for entry in root.findall("atom:entry", ns):
                        title = entry.find("atom:title", ns)
                        summary = entry.find("atom:summary", ns)
                        published = entry.find("atom:published", ns)
                        id_elem = entry.find("atom:id", ns)

                        authors = []
                        for author in entry.findall("atom:author", ns):
                            name_elem = author.find("atom:name", ns)
                            if name_elem is not None and name_elem.text:
                                authors.append(name_elem.text.strip())

                        clean_title = title.text.replace("\n", " ").strip() if title is not None and title.text else "arXiv Paper"
                        clean_summary = summary.text.replace("\n", " ").strip() if summary is not None and summary.text else ""
                        pub_year = None
                        if published is not None and published.text:
                            try:
                                pub_year = int(published.text[:4])
                            except Exception:
                                pass

                        paper_url = id_elem.text.strip() if id_elem is not None and id_elem.text else "https://arxiv.org"

                        results.append({
                            "id": f"arxiv-{len(results)+1}",
                            "title": clean_title,
                            "authors": authors[:5],
                            "url": paper_url,
                            "snippet": clean_summary[:600],
                            "source_type": "academic_db",
                            "published_year": pub_year,
                            "journal_or_domain": "arxiv.org",
                            "is_peer_reviewed": False,  # arXiv hosts preprints
                        })
        except Exception as e:
            logger.warning(f"arXiv search error: {e}")

        return results

    async def search_academic_semanticscholar(self, query: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Queries Semantic Scholar Academic Graph API."""
        results = []
        try:
            url = "https://api.semanticscholar.org/graph/v1/paper/search"
            params = {
                "query": query,
                "limit": max_results,
                "fields": "title,authors,year,abstract,venue,citationCount,url,openAccessPdf"
            }
            async with httpx.AsyncClient(timeout=8.0) as client:
                resp = await client.get(url, params=params)
                if resp.status_code == 200:
                    data = resp.json()
                    papers = data.get("data", [])
                    for p in papers:
                        authors = [a.get("name") for a in p.get("authors", []) if a.get("name")]
                        abstract = p.get("abstract") or "Abstract not indexed."
                        venue = p.get("venue") or "Semantic Scholar"
                        paper_url = p.get("url") or (p.get("openAccessPdf") or {}).get("url") or "https://semanticscholar.org"

                        results.append({
                            "id": f"s2-{str(p.get('paperId') or len(results) + 1)[:8]}",
                            "title": p.get("title") or "Untitled Academic Paper",
                            "authors": authors[:4],
                            "url": paper_url,
                            "snippet": abstract[:600],
                            "source_type": "academic_db",
                            "published_year": p.get("year"),
                            "journal_or_domain": venue,
                            "is_peer_reviewed": True,
                            "citation_count": p.get("citationCount"),
                        })
        except Exception as e:
            logger.warning(f"Semantic Scholar search error: {e}")

        return results

    def _tavily_search_sync(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        from tavily import TavilyClient
        response = TavilyClient(api_key=self.tavily_key).search(
            query=query, search_depth="advanced", max_results=max_results
        )
        results = []
        for item in response.get("results", []):
            url = item.get("url", "")
            results.append({
                "id": f"web-{len(results)+1}",
                "title": item.get("title", "Web Result"),
                "authors": [],
                "url": url,
                "snippet": item.get("content", "")[:500],
                "source_type": "live_web",
                "journal_or_domain": url.split("/")[2] if "://" in url else "web",
                "is_peer_reviewed": False,
            })
        return results

    def _ddg_search_sync(self, query: str, max_results: int) -> List[Dict[str, Any]]:
        from duckduckgo_search import DDGS
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=max_results):
                url = r.get("href", "")
                results.append({
                    "id": f"ddg-{len(results)+1}",
                    "title": r.get("title", "Web Result"),
                    "authors": [],
                    "url": url,
                    "snippet": r.get("body", "")[:500],
                    "source_type": "live_web",
                    "journal_or_domain": url.split("/")[2] if "://" in url else "web",
                    "is_peer_reviewed": False,
                })
        return results

    async def search_live_web(self, query: str, max_results: int = 6) -> List[Dict[str, Any]]:
        """Live web search (Tavily if configured, else DuckDuckGo). The SDKs are
        synchronous, so they run in worker threads to keep the event loop free."""
        if self.tavily_key:
            try:
                results = await asyncio.to_thread(self._tavily_search_sync, query, max_results)
                if results:
                    return results
            except Exception as e:
                logger.warning(f"Tavily search failed, falling back to DuckDuckGo: {e}")
        try:
            return await asyncio.to_thread(self._ddg_search_sync, query, max_results)
        except Exception as e:
            logger.warning(f"DuckDuckGo search error: {e}")
            return []

    async def search_all_external(self, query: str) -> List[Dict[str, Any]]:
        """Concurrent gathering from all external sources."""
        academic_tasks = [
            self.search_academic_arxiv(query, max_results=4),
            self.search_academic_semanticscholar(query, max_results=4),
            self.search_live_web(query, max_results=5),
        ]
        gathered = await asyncio.gather(*academic_tasks, return_exceptions=True)

        combined: List[Dict[str, Any]] = []
        for res in gathered:
            if isinstance(res, list):
                combined.extend(res)
        return combined
