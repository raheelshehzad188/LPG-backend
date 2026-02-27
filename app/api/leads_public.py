from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.lead import Lead
from app.schemas.lead import LeadSaveRequest

router = APIRouter(prefix="/api", tags=["Leads - Public"])


@router.post("/leads")
def save_lead(data: LeadSaveRequest, db: Session = Depends(get_db)):
    lead = Lead(
        name=data.name or "Web Visitor",
        phone=data.phone,
        context=data.context,
        source="AI Chat",
    )
    db.add(lead)
    db.commit()
    db.refresh(lead)
    return {"success": True, "id": lead.id}
