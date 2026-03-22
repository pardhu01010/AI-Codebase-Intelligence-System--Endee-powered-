import inngest
import inngest.fast_api
import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

from llm import generate_answer
from retrieval import format_context, retrieve_context
from workflow import ingest_github_repo, inngest_client

app = FastAPI(title="AI Codebase Intelligence API")

inngest.fast_api.serve(app, inngest_client, [ingest_github_repo])


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
    context_chunks = retrieve_context(request.query, top_k=5)
    formatted_context = format_context(context_chunks)

    if "No relevant context" in formatted_context:
        return {
            "answer": "I don't have enough information about this codebase yet. Have you ingested the repository?",
            "sources": [],
        }

    answer = generate_answer(request.query, formatted_context)
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
