"""DB mein current Gemini prompt (LEAD_COLLECT_PROMPT) update karein."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal
from app.models.gemini_settings import GeminiSettings
from app.core.ai_engine import LEAD_COLLECT_PROMPT

db = SessionLocal()
settings = db.query(GeminiSettings).first()
if not settings:
    settings = GeminiSettings()
    db.add(settings)
    db.flush()

settings.system_instructions = LEAD_COLLECT_PROMPT
db.commit()
db.refresh(settings)
db.close()
print("✅ Gemini prompt DB mein update ho gaya (system_instructions).")
