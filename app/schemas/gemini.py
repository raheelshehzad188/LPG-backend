from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class GeminiSettingsSaveRequest(BaseModel):
    """Frontend camelCase bhejta hai — aliases accept karo."""
    api_key: Optional[str] = Field(None, alias="apiKey")
    system_instructions: Optional[str] = Field(None, alias="systemInstructions")
    conversation_instructions: Optional[str] = Field(None, alias="conversationInstructions")
    model: Optional[str] = None

    model_config = {"populate_by_name": True}  # alias ya field name dono accept


class GeminiSettingsResponse(BaseModel):
    api_key: Optional[str] = None
    api_key_masked: Optional[str] = None
    system_instructions: Optional[str] = None
    conversation_instructions: Optional[str] = None
    model: Optional[str] = None
    updated_at: Optional[datetime] = None


class GeminiTestRequest(BaseModel):
    api_key: Optional[str] = None
