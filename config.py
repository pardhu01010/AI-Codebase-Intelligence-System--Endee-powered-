import os
from pathlib import Path

from dotenv import load_dotenv

# Single env file at project root (same for uvicorn, Streamlit, Inngest workers).
_ROOT = Path(__file__).resolve().parent
load_dotenv(_ROOT / ".env")

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN", "")
# FastAPI + Inngest use port 8000 by default; run Endee on another port (e.g. Docker 8001).
ENDEE_URL = os.getenv("ENDEE_URL", "http://localhost:8001")
# Streamlit calls this for /ingest and /query (same host/port as uvicorn).
API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
# Event key can be a dev placeholder; Inngest Cloud needs a real key.
INNGEST_EVENT_KEY = os.getenv("INNGEST_EVENT_KEY", "local")
# Signing key must be a real Inngest signing key (hex) or omitted. Placeholders like
# "local" break the SDK (hash_signing_key) and cause /api/inngest sync to 500.
# Inngest() uses `signing_key or os.getenv("INNGEST_SIGNING_KEY")`, so we must remove
# invalid values from the environment or the client still picks them up.
_sk = os.getenv("INNGEST_SIGNING_KEY", "").strip()
if not _sk or _sk.lower() in ("local", "test", "dev"):
    os.environ.pop("INNGEST_SIGNING_KEY", None)
    INNGEST_SIGNING_KEY = None
else:
    INNGEST_SIGNING_KEY = _sk
INNGEST_DEV = os.getenv("INNGEST_DEV", "1") == "1"
