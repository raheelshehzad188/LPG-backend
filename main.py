from fastapi import FastAPI, Request, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.core.ai_engine import get_ai_response
from app.db.session import get_db, engine, Base
from app.models import Lead, Property, Admin, Agent, ScrapingSource, GeminiSettings  # noqa: F401 - register tables
from app.api.auth import router as auth_router
from app.api.admin_leads import router as admin_leads_router
from app.api.admin_agents import router as admin_agents_router
from app.api.admin_scraping import router as admin_scraping_router
from app.api.gemini import router as gemini_router
from app.api.leads_public import router as leads_public_router
from app.api.partner import router as partner_router

app = FastAPI(title="Lahore Property Guide API")

# CORS Fix for Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables
Base.metadata.create_all(bind=engine)

# Include routers
app.include_router(auth_router)
app.include_router(admin_leads_router)
app.include_router(admin_agents_router)
app.include_router(admin_scraping_router)
app.include_router(gemini_router)
app.include_router(leads_public_router)
app.include_router(partner_router)


@app.post("/api_new_ai")
async def chat_endpoint(request: Request, db: Session = Depends(get_db)):
    data = await request.json()
    query = data.get("query")
    messages = data.get("messages", [])

    from app.models.gemini_settings import GeminiSettings
    settings = db.query(GeminiSettings).first()

    try:
        ai_data = await get_ai_response(query, messages, db=db, gemini_settings=settings)
        return ai_data
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"question": "Internal Server Error", "listings": [], "message": "", "lead_info": None, "lead_id": None}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
