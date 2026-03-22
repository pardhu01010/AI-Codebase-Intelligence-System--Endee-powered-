import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv


def _endpoint_host_port(url: str) -> tuple[str, int]:
    p = urlparse((url or "").strip())
    host = (p.hostname or "").lower()
    if host in ("localhost", "::1"):
        host = "127.0.0.1"
    if not host:
        return "", 0
    port = p.port
    if port is None:
        port = 443 if (p.scheme or "http") == "https" else 80
    return host, port


# Single env file at project root (same for uvicorn, Streamlit, Inngest workers).
_ROOT = Path(__file__).resolve().parent
# override=True: a stale ENDEE_URL (or other var) in the OS/shell must not beat this file.
load_dotenv(_ROOT / ".env", override=True)

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
# SDK internal HTTP client timeout (ms). Ingest steps can be slow (clone, embed).
INNGEST_REQUEST_TIMEOUT_MS = int(os.getenv("INNGEST_REQUEST_TIMEOUT_MS", "600000"))


def endee_url_collides_with_api() -> bool:
    """True when ENDEE_URL points at the same host+port as FastAPI (common misconfiguration)."""
    return _endpoint_host_port(ENDEE_URL) == _endpoint_host_port(API_BASE_URL)
