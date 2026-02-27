from sqlalchemy import Column, Integer, String, Numeric, Text, DateTime
from app.db.session import Base
import datetime

class Property(Base):
    __tablename__ = "properties"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))
    location_name = Column(String(100))
    price = Column(Numeric(15, 2))
    area_size = Column(String(50))
    type = Column(String(50))
    description = Column(Text)
    cover_photo = Column(String(255))
    bedrooms = Column(Integer)
    baths = Column(Integer)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)