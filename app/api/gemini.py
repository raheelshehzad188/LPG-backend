import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import google.generativeai as genai

from app.db.session import get_db
from app.models.gemini_settings import GeminiSettings
from app.core.config import get_gemini_model as _get_gemini_model
from app.core.ai_engine import invalidate_gemini_cache
from app.api.deps import get_admin_from_token
from app.schemas.gemini import GeminiSettingsSaveRequest, GeminiTestRequest

router = APIRouter(prefix="/api", tags=["Gemini"])

DEFAULT_SYSTEM = "Lahore Property Guide AI. Max 1-2 lines per reply. No lists, no bullets, no long advice. Sirf short question ya jawab."
DEFAULT_CONVERSATION = "Ek question per reply. Short. Order: type→budget→location→naam→phone."


def _mask_key(key: str) -> str:
    if not key or len(key) < 8:
        return "***"
    return key[:3] + "***" + key[-3:]


def _get_settings(db: Session) -> GeminiSettings | None:
    return db.query(GeminiSettings).first()


def _get_effective_key(db: Session) -> str | None:
    settings = _get_settings(db)
    if settings and settings.api_key:
        return settings.api_key
    return os.getenv("GEMINI_API_KEY")


@router.get("/gemini")
def get_gemini_settings(db: Session = Depends(get_db), admin=Depends(get_admin_from_token)):
    settings = _get_settings(db)
    key = _get_effective_key(db)
    return {
        "apiKey": None,
        "apiKeyMasked": _mask_key(key) if key else None,
        "systemInstructions": (settings.system_instructions or DEFAULT_SYSTEM) if settings else DEFAULT_SYSTEM,
        "conversationInstructions": (settings.conversation_instructions or DEFAULT_CONVERSATION) if settings else DEFAULT_CONVERSATION,
        "model": (settings.model or _get_gemini_model()) if settings else _get_gemini_model(),
        "updatedAt": settings.updated_at.isoformat() if settings and settings.updated_at else None,
    }


@router.put("/gemini")
def save_gemini_settings(data: GeminiSettingsSaveRequest, db: Session = Depends(get_db), admin=Depends(get_admin_from_token)):
    settings = _get_settings(db)
    if not settings:
        settings = GeminiSettings()
        db.add(settings)
        db.flush()
    if data.api_key is not None:
        settings.api_key = (data.api_key.strip() or None) if data.api_key else None
    if data.system_instructions is not None:
        settings.system_instructions = data.system_instructions
    if data.conversation_instructions is not None:
        settings.conversation_instructions = data.conversation_instructions
    if data.model is not None:
        settings.model = data.model
    db.commit()
    db.refresh(settings)
    invalidate_gemini_cache()  # naye instructions ke liye cache refresh
    return {"success": True}


@router.post("/gemini/test")
def test_gemini(data: GeminiTestRequest, db: Session = Depends(get_db), admin=Depends(get_admin_from_token)):
    key = data.api_key or _get_effective_key(db)
    if not key:
        return {"success": False, "error": "No API key provided"}
    try:
        genai.configure(api_key=key)
        settings = _get_settings(db)
        model_name = (settings.model if settings else None) or _get_gemini_model()
        if not model_name or model_name == "gemini-1.5-flash":
            model_name = _get_gemini_model()
        model = genai.GenerativeModel(model_name)
        model.generate_content("Hi")
        return {"success": True, "message": "Connection successful", "model": model_name}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/gemini/refresh-cache")
def refresh_gemini_cache(db: Session = Depends(get_db), admin=Depends(get_admin_from_token)):
    """Admin cache manually refresh kare — naya property data + instructions cache ho jayega."""
    invalidate_gemini_cache()
    return {"success": True, "message": "Cache invalidated. Next AI request will create fresh cache."}


@router.post("/gemini/reset")
def reset_gemini_instructions(db: Session = Depends(get_db), admin=Depends(get_admin_from_token)):
    settings = _get_settings(db)
    if not settings:
        settings = GeminiSettings()
        db.add(settings)
        db.flush()
    settings.system_instructions = DEFAULT_SYSTEM
    settings.conversation_instructions = DEFAULT_CONVERSATION
    db.commit()
    db.refresh(settings)
    invalidate_gemini_cache()  # default instructions ke liye cache refresh
    return {
        "success": True,
        "message": "Reset to default instructions",
        "systemInstructions": DEFAULT_SYSTEM,
        "conversationInstructions": DEFAULT_CONVERSATION,
    }
