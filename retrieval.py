from embeddings import generate_embedding
from endee_store import EndeeDB


def retrieve_context(
    query: str, filters: dict | None = None, top_k: int = 5
) -> list[dict]:
    query_emb = generate_embedding(query)
    db = EndeeDB()
    results = db.query(query_embedding=query_emb, top_k=top_k, filter_dict=filters)
    context_chunks = []
    if results:
        for res in results:
            meta = res.get("meta", {})
            context_chunks.append(meta)
    return context_chunks


def format_context(context_chunks: list[dict]) -> str:
    if not context_chunks:
        return "No relevant context found."
    formatted = "Below are relevant code snippets and information from the codebase:\n\n"
    for idx, chunk in enumerate(context_chunks):
        formatted += f"--- Snippet {idx + 1} ---\n"
        formatted += f"{chunk.get('content', '')}\n\n"
    return formatted
