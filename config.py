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
INNGEST_EVENT_KEY = os.getenv("INNGEST_EVENT_KEY", "local")
INNGEST_SIGNING_KEY = os.getenv("INNGEST_SIGNING_KEY", "local")
INNGEST_DEV = os.getenv("INNGEST_DEV", "1") == "1"
