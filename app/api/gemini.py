import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import google.generativeai as genai

from app.db.session import get_db
from app.models.gemini_settings import GeminiSettings
from app.api.deps import get_admin_from_token
from app.schemas.gemini import GeminiSettingsSaveRequest, GeminiTestRequest

router = APIRouter(prefix="/api", tags=["Gemini"])

DEFAULT_SYSTEM = "Tu Lahore Property Guide ka AI assistant ho. Users ko Lahore mein plots, houses, apartments dhundhne mein madad karo."
DEFAULT_CONVERSATION = "Ek ek question poocho, user ki requirements samajh kar property recommend karo."


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
        "model": (settings.model or "gemini-1.5-flash") if settings else os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-flash"),
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
    return {"success": True}


@router.post("/gemini/test")
def test_gemini(data: GeminiTestRequest, db: Session = Depends(get_db), admin=Depends(get_admin_from_token)):
    key = data.api_key or _get_effective_key(db)
    if not key:
        return {"success": False, "error": "No API key provided"}
    try:
        genai.configure(api_key=key)
        model = genai.GenerativeModel("gemini-1.5-flash")
        model.generate_content("Hi")
        return {"success": True, "message": "Connection successful", "model": "gemini-1.5-flash"}
    except Exception as e:
        return {"success": False, "error": str(e)}


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
    return {
        "success": True,
        "message": "Reset to default instructions",
        "systemInstructions": DEFAULT_SYSTEM,
        "conversationInstructions": DEFAULT_CONVERSATION,
    }
