from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class ScrapingSourceResponse(BaseModel):
    id: int
    source: str
    status: str
    last_run: Optional[datetime] = None
    listings: Optional[int] = None

    class Config:
        from_attributes = True


class ScrapingToggleRequest(BaseModel):
    status: str  # active | paused
