"""Central config — GEMINI_MODEL_NAME .env se fetch. Fallback sirf yahan."""
import os
from dotenv import load_dotenv

load_dotenv()


def get_gemini_model() -> str:
    """Env se model — .env mein GEMINI_MODEL_NAME set karo."""
    return (os.getenv("GEMINI_MODEL_NAME") or "").strip() or "gemini-3-flash-preview"
