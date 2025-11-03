
# -----------------------------------------------------------------------------------------------------------------------------------------------------------
#                                                     *****     Models     *****
# -----------------------------------------------------------------------------------------------------------------------------------------------------------


from sqlalchemy import Column, Integer, String, DateTime, Text
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

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    language = Column(String, default="en")
    interests = Column(Text, default="Technology")
    number = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)



from sqlalchemy import Column, Integer, String, DateTime, Text, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base

class Article(Base):
    __tablename__ = "articles"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    body = Column(Text)
    published_at = Column(DateTime)
    source = Column(String)
    url = Column(String, unique=True)
    location = Column(String)
    description = Column(String)
    # Relationships
    topics = relationship("ArticleTopic", back_populates="article")
    sentiment = relationship("Sentiment", uselist=False, back_populates="article")

class Topic(Base):
    __tablename__ = "topics"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    articles = relationship("ArticleTopic", back_populates="topic")

class ArticleTopic(Base):
    __tablename__ = "article_topics"
    id = Column(Integer, primary_key=True, index=True)
    article_id = Column(Integer, ForeignKey('articles.id'))
    topic_id = Column(Integer, ForeignKey('topics.id'))
    article = relationship("Article", back_populates="topics")
    topic = relationship("Topic", back_populates="articles")

class Sentiment(Base):
    __tablename__ = "sentiments"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    article_id = Column(Integer, ForeignKey('articles.id'))
    sentiment = Column(Float)
    sentiment_label = Column(String)
    article = relationship("Article", back_populates="sentiment")
