"""
MongoDB Atlas Vector Search Service for ARA.
Stores chunk embeddings and runs similarity search. If MongoDB / OpenAI are not
configured, every method is a harmless no-op and callers fall back to keyword search.
"""

import logging
from typing import List, Dict, Any, Optional

from backend.config import settings

logger = logging.getLogger(__name__)


class VectorStoreService:
    def __init__(self):
        self.mongodb_uri = settings.MONGODB_URI
        self._client = None
        self._collection = None
        self._vector_store = None
        self._init_failed = False

    def is_connected(self) -> bool:
        """True when Mongo and OpenAI are configured (needed to embed + search)."""
        return bool(
            self.mongodb_uri
            and "mongodb" in self.mongodb_uri
            and settings.OPENAI_API_KEY
            and not self._init_failed
        )

    def _get_store(self):
        if self._vector_store is not None:
            return self._vector_store
        if not self.is_connected():
            return None
        try:
            from pymongo import MongoClient
            from langchain_community.vectorstores import MongoDBAtlasVectorSearch
            from langchain_openai import OpenAIEmbeddings

            self._client = MongoClient(self.mongodb_uri, serverSelectionTimeoutMS=5000)
            self._collection = self._client[settings.MONGODB_DB_NAME][settings.MONGODB_COLLECTION]
            embeddings = OpenAIEmbeddings(
                model=settings.OPENAI_EMBEDDING_MODEL,
                openai_api_key=settings.OPENAI_API_KEY,
            )
            self._vector_store = MongoDBAtlasVectorSearch(
                collection=self._collection,
                embedding=embeddings,
                index_name=settings.MONGODB_INDEX_NAME,
            )
            logger.info("Connected to MongoDB Atlas Vector Search")
            return self._vector_store
        except Exception as e:
            logger.warning(f"Could not connect to MongoDB Atlas Vector Search: {e}")
            self._init_failed = True
            return None

    def add_chunks(self, texts: List[str], metadatas: List[Dict[str, Any]]) -> bool:
        """Embeds and stores chunks. Blocking - call via asyncio.to_thread from async code."""
        store = self._get_store()
        if not store or not texts:
            return False
        try:
            store.add_texts(texts=texts, metadatas=metadatas)
            return True
        except Exception as e:
            logger.error(f"Error inserting chunks into MongoDB Atlas: {e}")
            return False

    def similarity_search(self, query: str, k: int = 5, doc_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Vector search. Filters by doc_id in Python so no Atlas filter-index is required."""
        store = self._get_store()
        if not store:
            return []
        try:
            fetch_k = k * 4 if doc_ids else k
            hits = store.similarity_search_with_score(query, k=fetch_k)
            results = []
            for doc, score in hits:
                if doc_ids and doc.metadata.get("doc_id") not in doc_ids:
                    continue
                results.append({"text": doc.page_content, "metadata": doc.metadata, "score": float(score)})
            return results[:k]
        except Exception as e:
            logger.error(f"MongoDB vector search failed: {e}")
            return []

    def delete_document(self, doc_id: str) -> None:
        """Removes every stored chunk of a document."""
        if self._get_store() is None or self._collection is None:
            return
        try:
            self._collection.delete_many({"doc_id": doc_id})
        except Exception as e:
            logger.error(f"Failed to delete chunks of {doc_id} from MongoDB: {e}")


# Single shared instance (main.py and document_loader.py must use the same one)
vector_store = VectorStoreService()
