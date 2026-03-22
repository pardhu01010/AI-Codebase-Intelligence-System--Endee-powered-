# AI Codebase Intelligence

Ingest a GitHub repo (Python AST chunks → embeddings → **Endee**), then ask questions (**Groq** + retrieval). **Inngest** runs the ingestion workflow.

## Project files (repo root)

| File | Role |
|------|------|
| `main.py` | FastAPI + Inngest endpoints |
| `streamlit_app.py` | Streamlit UI |
| `workflow.py` | Ingestion pipeline |
| `ingestion.py` | Clone repo, list files |
| `ast_parser.py`, `chunks.py` | Parse Python, build chunks |
| `embeddings.py`, `endee_store.py` | Embeddings + Endee |
| `retrieval.py`, `llm.py` | Query + Groq |
| `config.py` | Environment variables |

## Run (three terminals)

Use **three terminals** from the project folder (after `uv sync`).

**Ports must match:** `uv run uvicorn main:app --reload` defaults to **port 8000** (host 127.0.0.1). Your Inngest CLI `-u` URL must use the **same** host and port (e.g. `http://127.0.0.1:8000/api/inngest`). If you use `--port 8080`, change the Inngest URL to `...8080/api/inngest` and set `API_BASE_URL` in `.env` accordingly.

**1 — Backend (FastAPI + Inngest routes on `/api/inngest`)**

```bash
uv run uvicorn main:app --reload --host 127.0.0.1 --port 8000
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
uv run streamlit run streamlit_app.py
```

The UI calls the API at `API_BASE_URL` (default `http://127.0.0.1:8000`). Override in `.env` if needed.

## Environment

There is **one** runtime file: **`.env`** in the project root (next to `config.py`). All processes load it via `config.py`, no matter which directory you start them from.

**`.env.example`** is only a template for GitHub: copy it once (`cp .env.example .env` on Unix, or copy/paste on Windows), then edit **`.env`**. The app never reads `.env.example`.

You will set **two URLs** in `.env` on purpose: **`ENDEE_URL`** is the Endee vector API; **`API_BASE_URL`** is where Streamlit finds this FastAPI app (same host/port as `uvicorn`).

- `GROQ_API_KEY` — required for answers
- `ENDEE_URL` — Endee API (default `http://localhost:8001` so it does not clash with FastAPI on **8000**)
- `API_BASE_URL` — where Streamlit sends `/ingest` and `/query` (default `http://127.0.0.1:8000`)
- Inngest: `INNGEST_EVENT_KEY`, `INNGEST_DEV`. For **local dev**, leave **`INNGEST_SIGNING_KEY` empty** (do not set it to `local` — that is not a valid key and breaks the SDK during sync; a real Inngest signing key is hex-formatted).
- Optional: `GITHUB_TOKEN` for private repos
