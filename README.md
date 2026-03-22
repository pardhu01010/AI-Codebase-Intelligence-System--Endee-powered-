# AI Codebase Intelligence

Ingest a GitHub repo (Python AST chunks → embeddings → **Endee**), then ask questions (**Groq** + retrieval). **Inngest** runs the ingestion workflow.

## Project files (repo root)

| File | Role |
|------|------|
| `main.py` | FastAPI + Inngest endpoints |
| `app.py` | Streamlit UI |
| `workflow.py` | Ingestion pipeline |
| `ingestion.py` | Clone repo, list files |
| `ast_parser.py`, `chunks.py` | Parse Python, build chunks |
| `embeddings.py`, `endee_store.py` | Embeddings + Endee |
| `retrieval.py`, `llm.py` | Query + Groq |
| `config.py` | Environment variables |

## Run (three terminals)

Use **three terminals** from the project folder (after `uv sync`).

**Two different servers, two ports:**

| Service | Typical URL | Role |
|--------|----------------|------|
| **FastAPI** (this repo) | `http://127.0.0.1:8000` | `/ingest`, `/query`, `/api/inngest` |
| **Endee** (vector DB) | `http://127.0.0.1:8001` | `/api/v1/index/...` |

`ENDEE_URL` must point at **Endee only**. If you set it to port **8000** (same as uvicorn), the app will call `GET /api/v1/index/list` on **FastAPI**, which returns **404** — that is the error you see.

**Inngest CLI** `-u` must match **FastAPI** (e.g. `http://127.0.0.1:8000/api/inngest`), not Endee.

The dashboard may show `localhost:8000` for the app — that is the same machine as `127.0.0.1:8000` for the API only.

**Avoid `--reload` while debugging long ingests:** reload restarts the worker and **drops in-flight Inngest HTTP calls** (`connection forcibly closed`). Use `uv run uvicorn main:app --host 127.0.0.1 --port 8000` without reload for stable runs.

**1 — Backend (FastAPI + Inngest routes on `/api/inngest`)**

```bash
uv run uvicorn main:app --host 127.0.0.1 --port 8000
```

Optional shortcut (same defaults):

```bash
uv run python main.py
```

**2 — Inngest dev server** (points at your app’s Inngest endpoint)

```bash
npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest
```

**3 — Streamlit UI**

```bash
uv run streamlit run app.py
```

The UI calls the API at `API_BASE_URL` (default `http://127.0.0.1:8000`). Override in `.env` if needed.

## Environment

There is **one** runtime file: **`.env`** in the project root (next to `config.py`). All processes load it via `config.py`, no matter which directory you start them from.

**`.env.example`** is only a template for GitHub: copy it once (`cp .env.example .env` on Unix, or copy/paste on Windows), then edit **`.env`**. The app never reads `.env.example`.

You will set **two URLs** in `.env` on purpose: **`ENDEE_URL`** is the Endee vector API; **`API_BASE_URL`** is where Streamlit finds this FastAPI app (same host/port as `uvicorn`).

- `GROQ_API_KEY` — required for answers
- `ENDEE_URL` — Endee API (default `http://localhost:8001` so it does not clash with FastAPI on **8000**)
- `API_BASE_URL` — where Streamlit sends `/ingest` and `/query` (default `http://127.0.0.1:8000`)
- Inngest: `INNGEST_EVENT_KEY`, `INNGEST_DEV`, optional `INNGEST_REQUEST_TIMEOUT_MS` (default **600000** = 10 minutes for the SDK HTTP client). For **local dev**, leave **`INNGEST_SIGNING_KEY` empty** (do not use `local` — not valid hex; breaks sync).
- Optional: `GITHUB_TOKEN` for private repos

## Troubleshooting

- **Inngest UI flips to “can’t find your application” while ingest runs** — Heavy work (git clone, embeddings, Endee HTTP) used to run on the asyncio event loop and **blocked Uvicorn**, so sync probes to `/api/inngest` timed out. Ingest steps now use `asyncio.to_thread` so the API stays responsive. **`POST .../api/inngest` returning `206 Partial Content` is normal** (streaming step execution), not a disconnect.
- **Use the same host in the CLI as in the browser when possible** — e.g. `npx inngest-cli@latest dev -u http://127.0.0.1:8000/api/inngest` with `uvicorn` on `127.0.0.1:8000`. Mixing `localhost` vs `127.0.0.1` can confuse some setups (Docker/WSL).
- **Ingest shows “No python code found to index” but the repo has Python files** — an older bug ran `cleanup_repo` inside `finally`, so Inngest could execute cleanup *before* reading files (deleting the clone). That is fixed; re-run ingest after pulling the latest `workflow.py`.
- **Streamlit search says no context** — Usually the index is empty (failed ingest or Endee down). Confirm Endee is reachable at `ENDEE_URL` and the Inngest run ends with `Success` and a positive `indexed_chunks`.
- **`NotFoundException` / index not found on embed** — Fixed a bug where `list_indexes()` results were read with the wrong field (`index_name` only). The client now accepts `name` or `index_name`. Ensure `ENDEE_URL` has **no** trailing path (e.g. `http://localhost:8001`); the code appends `/api/v1` automatically.
- **`.env` says `8001` but errors still show `8000`** — Windows or your shell may define `ENDEE_URL` globally; `python-dotenv` used to leave that in place. This project now loads `.env` with **`override=True`** so the file wins. After updating, **restart** uvicorn and Streamlit. You can check with: `uv run python -c "from config import ENDEE_URL; print(ENDEE_URL)"`.
