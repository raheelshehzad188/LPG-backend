"""Seed admin user and sample scraping sources."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import SessionLocal, engine, Base
from app.models import Admin, Agent, ScrapingSource, GeminiSettings, Lead, Property
from app.core.security import hash_password

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# Default admin: admin@lpg.com / admin123
if not db.query(Admin).first():
    admin = Admin(email="admin@lpg.com", password_hash=hash_password("admin123"), name="Admin")
    db.add(admin)
    db.commit()
    print("Created admin: admin@lpg.com / admin123")

# Sample agent for partner login: ahmed@eliteproperties.com / secret123
if not db.query(Agent).first():
    agent = Agent(
        agent_name="Ahmed Khan",
        agency_name="Elite Properties",
        email="ahmed@eliteproperties.com",
        password_hash=hash_password("secret123"),
        phone="+92 300 1234567",
        specialization="DHA Phase 9, Gulberg III",
        status="active",
        routing_enabled=True,
    )
    db.add(agent)
    db.commit()
    print("Created agent: ahmed@eliteproperties.com / secret123")

# Sample scraping sources
if not db.query(ScrapingSource).first():
    for name in ["DHA Phase 9", "Bahria Town"]:
        db.add(ScrapingSource(source=name, status="active", listings=0))
    db.commit()
    print("Created scraping sources")

db.close()
print("Init complete.")
