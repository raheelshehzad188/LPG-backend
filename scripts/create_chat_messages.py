"""Create chat_messages table if not exists."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from app.db.session import engine
from app.models.chat_message import ChatMessage
from app.db.session import Base

Base.metadata.create_all(bind=engine)
print("chat_messages table ready")
