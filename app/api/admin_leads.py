from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.lead import Lead
from app.models.agent import Agent
from app.api.deps import get_admin_from_token
from app.schemas.lead import LeadRerouteRequest

router = APIRouter(prefix="/api/admin", tags=["Admin - Leads"])


@router.get("/leads")
def list_leads(
    db: Session = Depends(get_db),
    admin=Depends(get_admin_from_token),
    status: str | None = Query(None),
    agent_id: int | None = Query(None, alias="agentId"),
    from_date: str | None = Query(None, alias="from"),
    to_date: str | None = Query(None, alias="to"),
):
    q = db.query(Lead)
    if status:
        q = q.filter(Lead.status == status)
    if agent_id:
        q = q.filter(Lead.assigned_agent_id == agent_id)
    if from_date:
        q = q.filter(Lead.created_at >= from_date)
    if to_date:
        q = q.filter(Lead.created_at <= to_date)
    leads = q.order_by(Lead.created_at.desc()).all()
    out = []
    for L in leads:
        agent = db.query(Agent).filter(Agent.id == L.assigned_agent_id).first() if L.assigned_agent_id else None
        out.append({
            "id": f"L{L.id}",
            "userName": L.user_name or L.name or "",
            "name": L.name or L.user_name or "",
            "phone": L.phone or "",
            "propertyInterest": L.property_interest or "",
            "propertyId": L.property_id or "",
            "propertyLink": L.property_link or "",
            "budget": L.budget or "",
            "leadScore": L.lead_score or 0,
            "assignedAgent": agent.agent_name if agent else "",
            "assignedAgentId": f"A{agent.id}" if agent else None,
            "status": L.status or "new",
            "aiSummary": L.ai_summary or "",
            "createdAt": L.created_at.isoformat() if L.created_at else None,
        })
    return {"leads": out}


@router.post("/leads/{lead_id}/reroute")
def reroute_lead(
    lead_id: str,
    data: LeadRerouteRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_from_token),
):
    lid = int(lead_id.replace("L", "")) if isinstance(lead_id, str) and lead_id.startswith("L") else int(lead_id)
    lead = db.query(Lead).filter(Lead.id == lid).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    aid = data.agent_id
    if aid is None and data.agentId:
        aid = int(str(data.agentId).replace("A", ""))
    if aid is None:
        raise HTTPException(status_code=400, detail="agentId required")
    agent = db.query(Agent).filter(Agent.id == aid).first()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    lead.assigned_agent_id = agent.id
    db.commit()
    db.refresh(lead)
    return {
        "success": True,
        "lead": {
            "id": f"L{lead.id}",
            "assignedAgentId": f"A{agent.id}",
            "assignedAgent": agent.agent_name,
        },
    }
