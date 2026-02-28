from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.admin_settings import AdminSettings
from app.api.deps import get_admin_from_token
from app.schemas.admin_settings import AdminSettingsUpdate

router = APIRouter(prefix="/api/admin", tags=["Admin - Settings"])

DEFAULT_LEAD_EXPIRE_MINUTES = 5
SETTINGS_KEY_LEAD_EXPIRE = "lead_expire_minutes"


def get_lead_expire_minutes(db: Session) -> tuple[int, datetime | None]:
    """Returns (minutes, updated_at). Default 5, None for updated_at if never set."""
    row = db.query(AdminSettings).filter(AdminSettings.key == SETTINGS_KEY_LEAD_EXPIRE).first()
    if not row or row.value is None:
        return DEFAULT_LEAD_EXPIRE_MINUTES, None
    try:
        return int(row.value), row.updated_at
    except ValueError:
        return DEFAULT_LEAD_EXPIRE_MINUTES, row.updated_at


@router.get("/settings")
def get_settings(
    db: Session = Depends(get_db),
    admin=Depends(get_admin_from_token),
):
    minutes, updated_at = get_lead_expire_minutes(db)
    return {
        "leadExpireMinutes": minutes,
        "updatedAt": updated_at.isoformat() if updated_at else None,
    }


@router.put("/settings")
def save_settings(
    data: AdminSettingsUpdate,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_from_token),
):
    minutes = data.leadExpireMinutes
    if not (1 <= minutes <= 60):
        raise HTTPException(
            status_code=400,
            detail="leadExpireMinutes must be between 1 and 60",
        )
    row = db.query(AdminSettings).filter(AdminSettings.key == SETTINGS_KEY_LEAD_EXPIRE).first()
    if row:
        row.value = str(minutes)
        row.updated_at = datetime.now(timezone.utc)
    else:
        row = AdminSettings(key=SETTINGS_KEY_LEAD_EXPIRE, value=str(minutes))
        db.add(row)
    db.commit()
    db.refresh(row)
    return {
        "success": True,
        "settings": {
            "leadExpireMinutes": minutes,
            "updatedAt": row.updated_at.isoformat() if row.updated_at else None,
        },
    }
