from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.core.security import decode_token
from app.models.admin import Admin
from app.models.agent import Agent

security = HTTPBearer(auto_error=False)


def get_admin_from_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> Admin:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "admin":
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    admin_id = payload.get("sub")
    if not admin_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    admin = db.query(Admin).filter(Admin.id == int(admin_id)).first()
    if not admin:
        raise HTTPException(status_code=401, detail="Admin not found")
    return admin


def get_agent_from_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> Agent:
    if not credentials:
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    payload = decode_token(credentials.credentials)
    if not payload or payload.get("type") != "partner":
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    agent_id = payload.get("sub")
    if not agent_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    agent_id = str(agent_id)
    agent = db.query(Agent).filter(Agent.id == agent_id).first()
    if not agent:
        raise HTTPException(status_code=401, detail="Agent not found")
    return agent
