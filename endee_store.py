import hashlib

from endee import Endee

from config import ENDEE_URL
from embeddings import get_embedding_dimension


class EndeeDB:
    def __init__(self, index_name: str = "code_intelligence"):
        self.client = Endee(token=None)
        self.client.set_base_url(f"{ENDEE_URL}/api/v1")
        self.index_name = index_name
        self.dimension = get_embedding_dimension()
        self._ensure_index_exists()
        self.index = self.client.get_index(self.index_name)

    def _ensure_index_exists(self) -> None:
        try:
            indexes = self.client.list_indexes()
            if not any(idx.get("index_name") == self.index_name for idx in indexes):
                self.client.create_index(
                    name=self.index_name,
                    dimension=self.dimension,
                    space_type="cosine",
                )
        except Exception as e:
            print(f"Error ensuring index exists: {e}")

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
