import asyncio
import logging
from datetime import timedelta
from typing import Any

import inngest

from ast_parser import parse_python_file, parse_generic_file
from chunks import build_chunks
from config import (
    INNGEST_DEV,
    INNGEST_EVENT_KEY,
    INNGEST_REQUEST_TIMEOUT_MS,
    INNGEST_SIGNING_KEY,
)
from embeddings import generate_embeddings
from endee_store import EndeeDB
from ingestion import cleanup_repo, clone_repo, get_code_files

_log = logging.getLogger(__name__)

INGEST_STATUS = {"status": "idle"}

inngest_client = inngest.Inngest(
    app_id="endee_ai_project",
    event_key=INNGEST_EVENT_KEY,
    signing_key=INNGEST_SIGNING_KEY,
    is_production=not INNGEST_DEV,
    request_timeout=INNGEST_REQUEST_TIMEOUT_MS,
)


def _parse_and_chunk_sync(code_files: list[str]) -> list[dict[str, Any]]:
    all_chunks: list[dict[str, Any]] = []
    for file_path in code_files:
        if file_path.endswith(".py"):
            parsed_items = parse_python_file(file_path)
        else:
            parsed_items = parse_generic_file(file_path)
        
        if parsed_items:
            all_chunks.extend(build_chunks(parsed_items))
    return all_chunks


def _embed_and_insert_sync(chunks: list[dict[str, Any]]) -> int:
    db = EndeeDB()
    texts = [c["content"] for c in chunks]
    embeddings = generate_embeddings(texts)
    db.insert_chunks(chunks, embeddings)
    return len(chunks)


@inngest_client.create_function(
    fn_id="ingest_github_repo",
    trigger=inngest.TriggerEvent(event="repo/ingest"),
    timeouts=inngest.Timeouts(
        start=timedelta(minutes=10),
        finish=timedelta(hours=1),
    ),
)
async def ingest_github_repo(ctx: inngest.Context) -> dict:
    """SDK passes a single Context; step API is ctx.step (not a second argument)."""
    step = ctx.step
    raw = getattr(ctx.event, "data", None)
    data = raw if isinstance(raw, dict) else {}
    repo_url = data.get("repo_url")
    if not repo_url:
        return {"error": "Missing repo_url"}

    async def _clone():
        # git/subprocess blocks — must not hold the asyncio loop or Inngest sync fails.
        return await asyncio.to_thread(clone_repo, repo_url)

    repo_path = await step.run("clone_repo", _clone)

    async def _cleanup():
        await asyncio.to_thread(cleanup_repo, repo_path)

    try:

        async def _get_files():
            return await asyncio.to_thread(get_code_files, repo_path)

        code_files = await step.run("get_code_files", _get_files)

        async def _clear_index():
            def do_clear():
                db = EndeeDB()
                try:
                    db.client.delete_index(db.index_name)
                except Exception:
                    pass
                db._ensure_index_exists()
            return await asyncio.to_thread(do_clear)

        await step.run("clear_old_index", _clear_index)

        async def _parse_and_chunk():
            return await asyncio.to_thread(_parse_and_chunk_sync, code_files)

        all_chunks = await step.run("parse_and_chunk_files", _parse_and_chunk)

        if not all_chunks:
            await step.run("cleanup_repo", _cleanup)
            return {"status": "No python code found to index."}

        batch_size = 50
        for i in range(0, len(all_chunks), batch_size):
            batch_chunks = all_chunks[i : i + batch_size]

            async def _embed_and_insert(chunks: list[dict[str, Any]] = batch_chunks):
                try:
                    return await asyncio.to_thread(_embed_and_insert_sync, chunks)
                except Exception:
                    _log.exception("embed_and_insert_batch failed")
                    raise

            await step.run(f"embed_and_insert_batch_{i}", _embed_and_insert)

        await step.run("cleanup_repo", _cleanup)
        
        async def _mark_done():
            INGEST_STATUS["status"] = "completed"
        await step.run("mark_done", _mark_done)
        
        return {"status": "Success", "indexed_chunks": len(all_chunks)}

    except Exception as e:
        await step.run("cleanup_repo_after_error", _cleanup)
        
        async def _mark_error():
            INGEST_STATUS["status"] = "error"
        await step.run("mark_done_error", _mark_error)
        
        raise
