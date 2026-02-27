from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class AgentCreateRequest(BaseModel):
    agent_name: str
    agency_name: str
    email: str
    password: str
    phone: str = ""
    specialization: Optional[str] = None
    status: str = "active"


class AgentUpdateRequest(BaseModel):
    agent_name: Optional[str] = None
    agency_name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None
    phone: Optional[str] = None
    specialization: Optional[str] = None
    status: Optional[str] = None


class AgentResponse(BaseModel):
    id: int
    agent_name: str
    agency_name: str
    email: str
    phone: Optional[str] = None
    specialization: Optional[str] = None
    status: Optional[str] = None
    routing_enabled: Optional[bool] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AgentRoutingRequest(BaseModel):
    active: bool


class AgentPartnerResponse(BaseModel):
    id: int
    agent_name: str
    agency_name: str
    email: str
    phone: Optional[str] = None
