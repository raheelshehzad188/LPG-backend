from pathlib import Path

from fastapi import FastAPI, Request, Depends
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.ai_engine import get_ai_response
from app.db.session import get_db, engine, Base
from app.models import Lead, Property, Admin, Agent, ScrapingSource, GeminiSettings, ChatMessage, AdminSettings  # noqa: F401
from app.api.auth import router as auth_router
from app.api.admin_leads import router as admin_leads_router
from app.api.admin_agents import router as admin_agents_router
from app.api.admin_scraping import router as admin_scraping_router
from app.api.admin_settings import router as admin_settings_router
from app.api.gemini import router as gemini_router
from app.api.leads_public import router as leads_public_router
from app.api.partner import router as partner_router

app = FastAPI(title="Lahore Property Guide API")


@app.middleware("http")
async def add_noindex_header(request: Request, call_next):
    """Prevent Google/search engines from indexing this API."""
    response = await call_next(request)
    response.headers["X-Robots-Tag"] = "noindex, nofollow"
    return response


@app.get("/robots.txt", include_in_schema=False)
async def robots_txt():
    """Tell crawlers not to index this site."""
    return Response(
        content="User-agent: *\nDisallow: /\n",
        media_type="text/plain",
    )


# CORS Fix for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)


def _run_migrations():
    """Add assigned_at to leads if missing (fixes Internal Server Error after schema update)."""
    from sqlalchemy import text
    try:
        with engine.connect() as conn:
            conn.execute(text("ALTER TABLE leads ADD COLUMN assigned_at DATETIME(6) NULL"))
            conn.commit()
    except Exception as e:
        if "Duplicate column" not in str(e) and "already exists" not in str(e).lower():
            pass  # Ignore - column may already exist


@app.on_event("startup")
def startup_migration():
    try:
        _run_migrations()
    except Exception:
        pass  # Non-fatal - app runs even if migration fails

# Property images — /property/48012653_cover.jpg -> property_images/48012653_cover.jpg
_property_images_dir = Path(__file__).resolve().parent / "property_images"
if _property_images_dir.exists():
    app.mount("/property", StaticFiles(directory=str(_property_images_dir)), name="property")

# Include routers
app.include_router(auth_router)
app.include_router(admin_leads_router)
app.include_router(admin_agents_router)
app.include_router(admin_scraping_router)
app.include_router(admin_settings_router)
app.include_router(gemini_router)
app.include_router(leads_public_router)
app.include_router(partner_router)


@app.post("/api_new_ai")
async def chat_endpoint(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    query = data.get("query")
    messages = data.get("messages", [])
    thread_id = data.get("threadId") or data.get("thread_id")

    from app.models.gemini_settings import GeminiSettings
    settings = db.query(GeminiSettings).first()

    try:
        ai_data = await get_ai_response(query, messages, thread_id=thread_id, db=db, gemini_settings=settings)
        return ai_data
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"question": "Internal Server Error", "listings": [], "message": "", "lead_info": None, "lead_id": None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
