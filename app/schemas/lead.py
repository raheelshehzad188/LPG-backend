from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class LeadSaveRequest(BaseModel):
    phone: str
    name: Optional[str] = "Web Visitor"
    context: Optional[str] = None


class LeadResponse(BaseModel):
    id: int
    user_name: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    property_interest: Optional[str] = None
    property_id: Optional[str] = None
    property_link: Optional[str] = None
    budget: Optional[str] = None
    lead_score: Optional[int] = None
    assigned_agent: Optional[str] = None
    assigned_agent_id: Optional[int] = None
    status: Optional[str] = None
    ai_summary: Optional[str] = None
    source: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class LeadRerouteRequest(BaseModel):
    agent_id: int | None = None
    agentId: str | None = None  # Frontend may send "A2"


class LeadStatusUpdateRequest(BaseModel):
    status: str  # new | in_progress | site_visit | closed
