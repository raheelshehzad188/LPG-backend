"""Add assigned_at column to leads table. Run once if upgrading from old schema."""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.session import engine
from sqlalchemy import text

with engine.connect() as conn:
    try:
        conn.execute(text("ALTER TABLE leads ADD COLUMN assigned_at DATETIME(6) NULL AFTER assigned_agent_id"))
        conn.commit()
        print("Added assigned_at column to leads table.")
    except Exception as e:
        if "Duplicate column" in str(e) or "already exists" in str(e).lower():
            print("Column assigned_at already exists. Skipping.")
        else:
            raise
print("Done.")
