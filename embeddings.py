from typing import List

from sentence_transformers import SentenceTransformer

# Lazy singleton; swap model here when moving to jina-embeddings-code (dimension must match index).
_model: SentenceTransformer | None = None


def get_encoder() -> SentenceTransformer:
    global _model
    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")
    return _model


def get_embedding_dimension() -> int:
    return 384


def generate_embeddings(texts: List[str]) -> List[List[float]]:
    if not texts:
        return []
    encoder = get_encoder()
    embeddings = encoder.encode(texts, convert_to_numpy=True)
    return embeddings.tolist()


def generate_embedding(text: str) -> List[float]:
    encoder = get_encoder()
    embedding = encoder.encode(text, convert_to_numpy=True)
    return embedding.tolist()
