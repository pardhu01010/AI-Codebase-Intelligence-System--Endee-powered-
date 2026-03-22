import hashlib
from typing import Any

from endee import Endee
from endee.exceptions import NotFoundException

from config import API_BASE_URL, ENDEE_URL, endee_url_collides_with_api
from embeddings import get_embedding_dimension


def _base_url() -> str:
    return f"{ENDEE_URL.rstrip('/')}/api/v1"


def _normalize_index_list(raw: Any) -> list[dict[str, Any]]:
    if isinstance(raw, list):
        return [x for x in raw if isinstance(x, dict)]
    if isinstance(raw, dict):
        for key in ("indexes", "data", "items", "results"):
            inner = raw.get(key)
            if isinstance(inner, list):
                return [x for x in inner if isinstance(x, dict)]
    return []


def _index_names(entries: list[dict[str, Any]]) -> set[str]:
    names: set[str] = set()
    for idx in entries:
        n = idx.get("index_name") or idx.get("name")
        if n is not None:
            names.add(str(n))
    return names


class EndeeDB:
    def __init__(self, index_name: str = "code_intelligence"):
        if endee_url_collides_with_api():
            raise RuntimeError(
                "ENDEE_URL must not use the same host and port as your FastAPI app. "
                f"You have ENDEE_URL={ENDEE_URL!r} and API_BASE_URL={API_BASE_URL!r} — "
                "requests to /api/v1/index/list then hit uvicorn and return 404. "
                "Run the Endee vector DB on another port (e.g. 8001) and set "
                "ENDEE_URL=http://127.0.0.1:8001 (see README)."
            )
        self.client = Endee(token=None)
        self.client.set_base_url(_base_url())
        self.index_name = index_name
        self.dimension = get_embedding_dimension()
        self._ensure_index_exists()
        try:
            self.index = self.client.get_index(self.index_name)
        except NotFoundException as e:
            raise RuntimeError(
                f"Endee index {self.index_name!r} not found at {ENDEE_URL} after create. "
                f"Check ENDEE_URL, that the server is running, and API path /api/v1. "
                f"Original: {e}"
            ) from e

    def _ensure_index_exists(self) -> None:
        try:
            raw = self.client.list_indexes()
        except NotFoundException as e:
            raise RuntimeError(
                f"Endee list_indexes returned 404 at {_base_url()}. "
                "If ENDEE_URL matches your FastAPI port, you are calling the wrong server. "
                f"ENDEE_URL={ENDEE_URL!r}, API_BASE_URL={API_BASE_URL!r}. "
                f"Original: {e}"
            ) from e
        except Exception as e:
            raise RuntimeError(
                f"Cannot reach Endee list_indexes at {_base_url()}. "
                f"Is ENDEE_URL correct ({ENDEE_URL})? {e}"
            ) from e

        entries = _normalize_index_list(raw)
        names = _index_names(entries)
        if self.index_name in names:
            return

        try:
            self.client.create_index(
                name=self.index_name,
                dimension=self.dimension,
                space_type="cosine",
            )
        except Exception as e:
            msg = str(e).lower()
            if "exist" in msg or "already" in msg or "duplicate" in msg:
                return
            raise RuntimeError(
                f"Failed to create Endee index {self.index_name!r} at {ENDEE_URL}: {e}"
            ) from e

    def insert_chunks(self, chunks: list[dict], embeddings: list[list[float]]) -> None:
        if not chunks or not embeddings:
            return
        vectors_to_insert = []
        for chunk, embedding in zip(chunks, embeddings):
            content_hash = hashlib.md5(chunk["content"].encode()).hexdigest()
            doc_id = (
                f"{chunk['metadata']['file']}_{chunk['metadata']['type']}_"
                f"{chunk['metadata']['name']}_{content_hash}"
            )
            file_filter = str(chunk["metadata"].get("file", ""))[:50]
            type_filter = str(chunk["metadata"].get("type", ""))[:50]
            vectors_to_insert.append(
                {
                    "id": doc_id,
                    "vector": embedding,
                    "meta": {"content": chunk["content"], **chunk["metadata"]},
                    "filter": {"file": file_filter, "type": type_filter},
                }
            )
        try:
            self.index.upsert(vectors_to_insert)
            print(f"Successfully inserted {len(vectors_to_insert)} vectors.")
        except Exception as e:
            print(f"Failed to insert vectors: {e}")

    def query(
        self,
        query_embedding: list[float],
        top_k: int = 5,
        filter_dict: dict | None = None,
    ):
        try:
            return self.index.query(
                vector=query_embedding, top_k=top_k, filter=filter_dict
            )
        except Exception as e:
            print(f"Query failed: {e}")
            return []
