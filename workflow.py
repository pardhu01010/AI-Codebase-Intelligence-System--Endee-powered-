import inngest

from ast_parser import parse_python_file
from chunks import build_chunks
from config import INNGEST_DEV, INNGEST_EVENT_KEY, INNGEST_SIGNING_KEY
from embeddings import generate_embeddings
from endee_store import EndeeDB
from ingestion import cleanup_repo, clone_repo, get_code_files

inngest_client = inngest.Inngest(
    app_id="endee_ai_project",
    event_key=INNGEST_EVENT_KEY,
    signing_key=INNGEST_SIGNING_KEY,
    is_production=not INNGEST_DEV,
)


@inngest_client.create_function(
    fn_id="ingest_github_repo",
    trigger=inngest.TriggerEvent(event="repo/ingest"),
)
async def ingest_github_repo(ctx: inngest.Context) -> dict:
    """SDK passes a single Context; step API is ctx.step (not a second argument)."""
    step = ctx.step
    repo_url = ctx.event.data.get("repo_url")
    if not repo_url:
        return {"error": "Missing repo_url"}

    async def _clone():
        return clone_repo(repo_url)

    repo_path = await step.run("clone_repo", _clone)

    try:

        async def _get_files():
            return get_code_files(repo_path)

        code_files = await step.run("get_code_files", _get_files)

        async def _parse_and_chunk():
            all_chunks = []
            for file_path in code_files:
                if file_path.endswith(".py"):
                    parsed_items = parse_python_file(file_path)
                    if parsed_items:
                        chunks = build_chunks(parsed_items)
                        all_chunks.extend(chunks)
            return all_chunks

        all_chunks = await step.run("parse_and_chunk_files", _parse_and_chunk)

        if not all_chunks:
            return {"status": "No python code found to index."}

        batch_size = 50
        for i in range(0, len(all_chunks), batch_size):
            batch_chunks = all_chunks[i : i + batch_size]

            async def _embed_and_insert(chunks=batch_chunks):
                db = EndeeDB()
                texts = [c["content"] for c in chunks]
                embeddings = generate_embeddings(texts)
                db.insert_chunks(chunks, embeddings)
                return len(chunks)

            await step.run(f"embed_and_insert_batch_{i}", _embed_and_insert)

        return {"status": "Success", "indexed_chunks": len(all_chunks)}

    finally:

        async def _cleanup():
            cleanup_repo(repo_path)

        await step.run("cleanup_repo", _cleanup)
