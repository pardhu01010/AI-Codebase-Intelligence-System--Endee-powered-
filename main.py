import asyncio
from contextlib import asynccontextmanager

import inngest
import inngest.fast_api
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from embeddings import get_encoder
from llm import generate_answer
from retrieval import format_context, retrieve_context
from workflow import ingest_github_repo, inngest_client


@asynccontextmanager
async def lifespan(_app: FastAPI):
    # Load SentenceTransformer once so Inngest steps are not killed by first-run download.
    await asyncio.to_thread(get_encoder)
    yield


app = FastAPI(title="AI Codebase Intelligence API", lifespan=lifespan)

inngest.fast_api.serve(app, inngest_client, [ingest_github_repo])


@app.get("/health")
async def health():
    """Lightweight probe so dashboards and sync checks do not hit 404 on GET /."""
    return {"ok": True}


class IngestRequest(BaseModel):
    repo_url: str


class QueryRequest(BaseModel):
    query: str


@app.post("/ingest")
async def trigger_ingest(request: IngestRequest):
    await inngest_client.send(
        inngest.Event(name="repo/ingest", data={"repo_url": request.repo_url})
    )
    return {"message": "Ingestion started in the background."}


@app.post("/query")
async def query_codebase(request: QueryRequest):
    try:
        context_chunks = await asyncio.to_thread(
            retrieve_context, request.query, None, 5
        )
    except Exception as e:
        return {
            "answer": f"Search failed (check Endee is running and ENDEE_URL in .env): {e}",
            "sources": [],
        }

    formatted_context = format_context(context_chunks)

    if "No relevant context" in formatted_context:
        return {
            "answer": (
                "No matching code was found in the vector index. "
                "If you just ingested a repo, check the Inngest run output: "
                "ingest must finish with indexed_chunks > 0 (not “No python code found to index”)."
            ),
            "sources": [],
        }

    answer = await asyncio.to_thread(
        generate_answer, request.query, formatted_context
    )
    sources = []
    for chunk in context_chunks:
        source_info = (
            f"{chunk.get('file', 'Unknown')} ({chunk.get('type', 'snippet')} "
            f"'{chunk.get('name', '')}')"
        )
        if source_info not in sources:
            sources.append(source_info)

    return {"answer": answer, "sources": sources}


def main() -> None:
    # Prefer: uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)


if __name__ == "__main__":
    main()
