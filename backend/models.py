
# -----------------------------------------------------------------------------------------------------------------------------------------------------------
#                                                     *****     Models     *****
# -----------------------------------------------------------------------------------------------------------------------------------------------------------

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
    # keywords = Column(Text)

# ---------------------------------------------------------------------------
# New User model
# ---------------------------------------------------------------------------
from sqlalchemy import Column, Integer, String, Text
from .database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)   # NEW!!
    password = Column(String, nullable=False)
    language = Column(String, default="en")
    interests = Column(Text, default="Technology")



