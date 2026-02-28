from pydantic import BaseModel, Field


class AdminSettingsUpdate(BaseModel):
    leadExpireMinutes: int = Field(..., ge=1, le=60)


class AdminSettingsResponse(BaseModel):
    leadExpireMinutes: int
    updatedAt: str | None = None
