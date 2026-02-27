from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class GeminiSettingsResponse(BaseModel):
    api_key: Optional[str] = None
    api_key_masked: Optional[str] = None
    system_instructions: Optional[str] = None
    conversation_instructions: Optional[str] = None
    model: Optional[str] = None
    updated_at: Optional[datetime] = None


class GeminiSettingsSaveRequest(BaseModel):
    api_key: Optional[str] = None
    system_instructions: Optional[str] = None
    conversation_instructions: Optional[str] = None
    model: Optional[str] = None


class GeminiTestRequest(BaseModel):
    api_key: Optional[str] = None
