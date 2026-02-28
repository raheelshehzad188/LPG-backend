from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.db.session import Base


class Lead(Base):
    __tablename__ = "leads"

    id = Column(String(50), primary_key=True, index=True)
    user_name = Column(String(100), nullable=True)  # Display name
    name = Column(String(100), nullable=True)
    phone = Column(String(30), nullable=True)
    property_interest = Column(String(255), nullable=True)
    property_id = Column(String(50), nullable=True)
    property_link = Column(String(255), nullable=True)
    budget = Column(String(50), nullable=True)
    lead_score = Column(Integer, nullable=True, default=0)
    assigned_agent_id = Column(String(50), nullable=True)  # matches agents.id (varchar)
    assigned_at = Column(DateTime(timezone=True), nullable=True)  # when assigned to agent (for expiry)
    status = Column(String(30), default="new")  # new | contacted | site_visit | closed | in_progress
    ai_summary = Column(Text, nullable=True)
    context = Column(Text, nullable=True)  # For /api/leads save
    chat_history = Column(Text, nullable=True)
    source = Column(String(50), default="AI Search")
    thread_id = Column(String(100), nullable=True, index=True)  # links to chat thread
    created_at = Column(DateTime(timezone=True), server_default=func.now())
