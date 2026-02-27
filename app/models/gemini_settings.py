from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class GeminiSettings(Base):
    __tablename__ = "gemini_settings"

    id = Column(Integer, primary_key=True, index=True)
    api_key = Column(String(255), nullable=True)  # Encrypted/stored, null = use env
    system_instructions = Column(Text, nullable=True)
    conversation_instructions = Column(Text, nullable=True)
    model = Column(String(50), default="gemini-1.5-flash")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
