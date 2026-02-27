from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.scraping_source import ScrapingSource
from app.api.deps import get_admin_from_token
from app.schemas.scraping import ScrapingToggleRequest

router = APIRouter(prefix="/api/admin", tags=["Admin - Scraping"])


@router.get("/scraping")
def list_scraping_sources(
    db: Session = Depends(get_db),
    admin=Depends(get_admin_from_token),
):
    sources = db.query(ScrapingSource).order_by(ScrapingSource.id).all()
    return {
        "sources": [
            {
                "id": f"S{s.id}",
                "source": s.source,
                "status": s.status or "active",
                "lastRun": s.last_run.isoformat() if s.last_run else None,
                "listings": s.listings or 0,
            }
            for s in sources
        ]
    }


@router.patch("/scraping/{source_id}")
def toggle_scraping(
    source_id: str,
    data: ScrapingToggleRequest,
    db: Session = Depends(get_db),
    admin=Depends(get_admin_from_token),
):
    sid = int(source_id.replace("S", "")) if isinstance(source_id, str) and source_id.startswith("S") else int(source_id)
    src = db.query(ScrapingSource).filter(ScrapingSource.id == sid).first()
    if not src:
        raise HTTPException(status_code=404, detail="Scraping source not found")
    if data.status not in ("active", "paused"):
        raise HTTPException(status_code=400, detail="status must be 'active' or 'paused'")
    src.status = data.status
    db.commit()
    db.refresh(src)
    return {
        "success": True,
        "source": {"id": f"S{src.id}", "status": src.status},
    }
