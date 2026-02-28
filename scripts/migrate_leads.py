"""Add missing columns to existing leads table for LPG backend compatibility."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from sqlalchemy import text
from app.db.session import engine

alter_sql = [
    "ALTER TABLE leads ADD COLUMN name VARCHAR(100) NULL",
    "ALTER TABLE leads ADD COLUMN context TEXT NULL",
    "ALTER TABLE leads ADD COLUMN chat_history TEXT NULL",
]

with engine.connect() as c:
    for sql in alter_sql:
        col = sql.split("ADD COLUMN ")[1].split(" ")[0]
        try:
            c.execute(text(sql))
            c.commit()
            print(f"Added column: {col}")
        except Exception as e:
            if "Duplicate column" in str(e) or "1060" in str(e):
                print(f"Column {col} already exists, skip")
            else:
                print(f"Error adding {col}: {e}")
