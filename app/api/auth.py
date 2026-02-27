from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.admin import Admin
from app.models.agent import Agent
from app.core.security import verify_password, create_token
from app.schemas.auth import AdminLoginRequest, PartnerLoginRequest

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/admin/login")
def admin_login(data: AdminLoginRequest, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.email == data.email).first()
    if not admin or not verify_password(data.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token({"sub": str(admin.id), "type": "admin"})
    return {
        "token": token,
        "user": {
            "id": f"admin_{admin.id}",
            "email": admin.email,
            "name": admin.name or "Admin",
        },
    }


@router.post("/partner/login")
def partner_login(data: PartnerLoginRequest, db: Session = Depends(get_db)):
    agent = db.query(Agent).filter(Agent.email == data.email).first()
    if not agent or not verify_password(data.password, agent.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if agent.status == "suspended":
        raise HTTPException(status_code=403, detail="Account suspended")
    token = create_token({"sub": str(agent.id), "type": "partner"})
    return {
        "token": token,
        "agent": {
            "id": f"A{agent.id}",
            "agentName": agent.agent_name,
            "agencyName": agent.agency_name,
            "email": agent.email,
            "phone": agent.phone or "",
        },
    }
