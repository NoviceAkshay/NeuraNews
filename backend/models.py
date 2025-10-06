# backend/models.py
# backend/models.py
from sqlalchemy import Column, Integer, String, DateTime
from .database import Base
import datetime

class News(Base):
    __tablename__ = "news"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    source = Column(String)
    published_at = Column(DateTime)
    url = Column(String, unique=True)
    description = Column(String)
    image_url = Column(String, nullable=True)
    fetched_at = Column(DateTime, default=datetime.datetime.utcnow)

# ---------------------------------------------------------------------------
# New User model
# ---------------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)  # we'll hash passwords later
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

