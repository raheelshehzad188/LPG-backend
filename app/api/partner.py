from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.lead import Lead
from app.models.agent import Agent
from app.api.deps import get_agent_from_token
from app.api.admin_settings import get_lead_expire_minutes
from app.schemas.lead import LeadStatusUpdateRequest

router = APIRouter(prefix="/api/partner", tags=["Partner"])


def _unlink_expired_leads(db: Session) -> None:
    """Unlink leads whose status=new and assigned_agent_id set but expired."""
    minutes, _ = get_lead_expire_minutes(db)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    expired = db.query(Lead).filter(
        Lead.status == "new",
        Lead.assigned_agent_id.isnot(None),
        Lead.assigned_at.isnot(None),
        Lead.assigned_at < cutoff,
    ).all()
    for l in expired:
        l.assigned_agent_id = None
        l.assigned_at = None
    if expired:
        db.commit()


@router.get("/leads")
def get_my_leads(
    db: Session = Depends(get_db),
    agent=Depends(get_agent_from_token),
    status: str | None = Query(None),
):
    _unlink_expired_leads(db)
    # Match both agent.id and "A"+agent.id (in case assigned_agent_id was stored with A prefix)
    q = db.query(Lead).filter(
        or_(Lead.assigned_agent_id == agent.id, Lead.assigned_agent_id == f"A{agent.id}")
    )
    if status:
        q = q.filter(Lead.status == status)
    leads = q.order_by(Lead.created_at.desc()).all()
    minutes, _ = get_lead_expire_minutes(db)
    out = []
    for l in leads:
        assigned_at = l.assigned_at
        expires_at = None
        if assigned_at and l.status == "new":
            expires_at = (assigned_at + timedelta(minutes=minutes)).isoformat()
        out.append({
            "id": l.id if isinstance(l.id, str) else f"L{l.id}",
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
            "expiresAt": expires_at,
            "assignedAt": assigned_at.isoformat() if assigned_at else None,
        })
    return {"leads": out}


@router.post("/leads/{lead_id}/accept")
def accept_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    agent=Depends(get_agent_from_token),
):
    lid = str(lead_id)
    agent_match = or_(Lead.assigned_agent_id == agent.id, Lead.assigned_agent_id == f"A{agent.id}")
    lead = db.query(Lead).filter(Lead.id == lid, agent_match).first()
    if not lead and lid.startswith("L"):
        lead = db.query(Lead).filter(Lead.id == lid[1:], agent_match).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    # Expiry check: if status=new and past expiry -> unlink and return 410
    if lead.status == "new" and lead.assigned_at:
        minutes, _ = get_lead_expire_minutes(db)
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=minutes)
        if lead.assigned_at < cutoff:
            lead.assigned_agent_id = None
            lead.assigned_at = None
            db.commit()
            raise HTTPException(
                status_code=410,
                detail={
                    "error": "Lead expired. It has been unlinked and is no longer assigned to you.",
                    "code": "LEAD_EXPIRED",
                },
            )
    lead.status = "in_progress"
    db.commit()
    db.refresh(lead)
    return {"success": True, "lead": {"id": lead.id if isinstance(lead.id, str) else f"L{lead.id}", "status": lead.status}}


@router.post("/leads/{lead_id}/reject")
def reject_lead(
    lead_id: str,
    db: Session = Depends(get_db),
    agent=Depends(get_agent_from_token),
):
    lid = str(lead_id)
    agent_match = or_(Lead.assigned_agent_id == agent.id, Lead.assigned_agent_id == f"A{agent.id}")
    lead = db.query(Lead).filter(Lead.id == lid, agent_match).first()
    if not lead and lid.startswith("L"):
        lead = db.query(Lead).filter(Lead.id == lid[1:], agent_match).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    lead.assigned_agent_id = None
    lead.assigned_at = None
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
    lid = str(lead_id)
    agent_match = or_(Lead.assigned_agent_id == agent.id, Lead.assigned_agent_id == f"A{agent.id}")
    lead = db.query(Lead).filter(Lead.id == lid, agent_match).first()
    if not lead and lid.startswith("L"):
        lead = db.query(Lead).filter(Lead.id == lid[1:], agent_match).first()
    if not lead:
        raise HTTPException(status_code=404, detail="Lead not found")
    if data.status not in ("new", "in_progress", "site_visit", "closed"):
        raise HTTPException(status_code=400, detail="Invalid status")
    lead.status = data.status
    db.commit()
    db.refresh(lead)
    return {"success": True, "lead": {"id": lead.id if isinstance(lead.id, str) else f"L{lead.id}", "status": lead.status}}
