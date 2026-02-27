from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from app.db.session import Base


class ScrapingSource(Base):
    __tablename__ = "scraping_sources"

    id = Column(Integer, primary_key=True, index=True)
    source = Column(String(150), nullable=False)  # e.g. "DHA Phase 9", "Bahria Town"
    status = Column(String(20), default="active")  # active | paused
    last_run = Column(DateTime(timezone=True), nullable=True)
    listings = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
