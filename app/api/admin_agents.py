from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.agent import Agent
from app.api.deps import get_admin_from_token
from app.core.security import hash_password
from app.schemas.agent import AgentCreateRequest, AgentUpdateRequest, AgentRoutingRequest

router = APIRouter(prefix="/api/admin", tags=["Admin - Agents"])


@router.get("/agents")
def list_agents(
    db: Session = Depends(get_db),
    admin=Depends(get_admin_from_token),
    status: str | None = Query(None),
    search: str | None = Query(None),
):
    q = db.query(Agent)
    if status:
        q = q.filter(Agent.status == status)
    if search:
        s = f"%{search}%"
        q = q.filter(
            (Agent.agent_name.ilike(s)) | (Agent.agency_name.ilike(s))
        )
    agents = q.order_by(Agent.created_at.desc()).all()
    return {
        "agents": [
            {
                "id": f"A{a.id}",
                "agentName": a.agent_name,
                "agencyName": a.agency_name,
                "email": a.email,
                "phone": a.phone or "",
                "specialization": a.specialization or "",
                "status": a.status or "active",
                "routingEnabled": a.routing_enabled,
                "createdAt": a.created_at.isoformat() if a.created_at else None,
            }
            for a in agents
        ]
    }


@router.post("/agents")
def create_agent(
    data: AgentCreateRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_from_token),
):
    if db.query(Agent).filter(Agent.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    agent = Agent(
        agent_name=data.agent_name,
        agency_name=data.agency_name,
        email=data.email,
        password_hash=hash_password(data.password),
        phone=data.phone or None,
        specialization=data.specialization,
        status=data.status or "active",
        routing_enabled=True,
    )
    db.add(agent)
    db.commit()
    db.refresh(agent)
    return {
        "success": True,
        "agent": {
            "id": f"A{agent.id}",
            "agentName": agent.agent_name,
            "agencyName": agent.agency_name,
            "phone": agent.phone or "",
            "specialization": agent.specialization or "",
            "status": agent.status,
            "routingEnabled": agent.routing_enabled,
        },
    }


@router.patch("/agents/{agent_id}")
def update_agent(
    agent_id: str,
    data: AgentUpdateRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_from_token),
):
    aid = int(agent_id.replace("A", "")) if isinstance(agent_id, str) and agent_id.startswith("A") else int(agent_id)
    agent = db.query(Agent).filter(Agent.id == aid).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    if data.agent_name is not None:
        agent.agent_name = data.agent_name
    if data.agency_name is not None:
        agent.agency_name = data.agency_name
    if data.email is not None:
        existing = db.query(Agent).filter(Agent.email == data.email, Agent.id != aid).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already in use")
        agent.email = data.email
    if data.password is not None and len(data.password) >= 6:
        agent.password_hash = hash_password(data.password)
    if data.phone is not None:
        agent.phone = data.phone
    if data.specialization is not None:
        agent.specialization = data.specialization
    if data.status is not None:
        agent.status = data.status
    db.commit()
    db.refresh(agent)
    return {"success": True, "agent": {"id": f"A{agent.id}", "agentName": agent.agent_name}}


@router.delete("/agents/{agent_id}")
def delete_agent(
    agent_id: str,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_from_token),
):
    aid = int(agent_id.replace("A", "")) if isinstance(agent_id, str) and agent_id.startswith("A") else int(agent_id)
    agent = db.query(Agent).filter(Agent.id == aid).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    db.delete(agent)
    db.commit()
    return {"success": True, "message": "Agent deleted"}


@router.patch("/agents/{agent_id}/routing")
def toggle_agent_routing(
    agent_id: str,
    data: AgentRoutingRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_from_token),
):
    aid = int(agent_id.replace("A", "")) if isinstance(agent_id, str) and agent_id.startswith("A") else int(agent_id)
    agent = db.query(Agent).filter(Agent.id == aid).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    agent.routing_enabled = data.active
    db.commit()
    db.refresh(agent)
    return {"success": True, "agent": {"id": f"A{agent.id}", "routingEnabled": agent.routing_enabled}}
