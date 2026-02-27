from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.lead import Lead
from app.models.agent import Agent
from app.api.deps import get_agent_from_token
from app.schemas.lead import LeadStatusUpdateRequest

router = APIRouter(prefix="/api/partner", tags=["Partner"])


@router.get("/leads")
def get_my_leads(
    db: Session = Depends(get_db),
    agent=Depends(get_agent_from_token),
    status: str | None = Query(None),
):
    q = db.query(Lead).filter(Lead.assigned_agent_id == agent.id)
    if status:
        q = q.filter(Lead.status == status)
    leads = q.order_by(Lead.created_at.desc()).all()
    return {
        "leads": [
            {
                "id": f"L{l.id}",
                "userName": l.user_name or l.name or "",
                "name": l.name or l.user_name or "",
                "phone": l.phone or "",
                "propertyInterest": l.property_interest or "",
                "budget": l.budget or "",
                "leadScore": l.lead_score or 0,
                "status": l.status or "new",
                "aiSummary": l.ai_summary or "",
                "source": l.source or "AI Search",
                "createdAt": l.created_at.isoformat() if l.created_at else None,
            }
            for l in leads
        ]
    }


@router.post("/leads/{lead_id}/accept")
def accept_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    agent=Depends(get_agent_from_token),
):
    lid = int(lead_id.replace("L", "")) if isinstance(lead_id, str) and lead_id.startswith("L") else int(lead_id)
    lead = db.query(Lead).filter(Lead.id == lid, Lead.assigned_agent_id == agent.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.status = "in_progress"
    db.commit()
    db.refresh(lead)
    return {"success": True, "lead": {"id": f"L{lead.id}", "status": lead.status}}


@router.post("/leads/{lead_id}/reject")
def reject_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    agent=Depends(get_agent_from_token),
):
    lid = int(lead_id.replace("L", "")) if isinstance(lead_id, str) and lead_id.startswith("L") else int(lead_id)
    lead = db.query(Lead).filter(Lead.id == lid, Lead.assigned_agent_id == agent.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.assigned_agent_id = None
    lead.status = "new"
    db.commit()
    return {"success": True, "message": "Lead rejected"}


@router.patch("/leads/{lead_id}")
def update_lead_status(
    lead_id: str,
    data: LeadStatusUpdateRequest,
    db: Session = Depends(get_db),
    agent=Depends(get_agent_from_token),
):
    lid = int(lead_id.replace("L", "")) if isinstance(lead_id, str) and lead_id.startswith("L") else int(lead_id)
    lead = db.query(Lead).filter(Lead.id == lid, Lead.assigned_agent_id == agent.id).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if data.status not in ("new", "in_progress", "site_visit", "closed"):
        raise HTTPException(status_code=400, detail="Invalid status")
    lead.status = data.status
    db.commit()
    db.refresh(lead)
    return {"success": True, "lead": {"id": f"L{lead.id}", "status": lead.status}}
