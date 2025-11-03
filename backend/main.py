


# main.py (clean, consolidated)

from fastapi import FastAPI, Query, HTTPException, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List
from datetime import datetime, timedelta
from dateutil import parser as dtparser
import numpy as np
from sqlalchemy import func

from backend.database import SessionLocal
from backend.models import User, News, Article, Topic, ArticleTopic, Sentiment
from backend.auth_service import register_user, login_user
from backend.text_cleaning import preprocess_text
from backend.keyword_extractor import extract_keywords, extract_keywords_from_texts
from backend.news_service import fetch_news
from backend.sentement_analyzer import NewsSentimentEmotionAnalyzer
from backend.ner_analyzer import NewsNerAnalyzer
from backend.topic_modeling import get_topics_from_articles
# # near the top with other imports
# from backend.admin_routes import admin as admin_router
# main.py (add after other imports)
from backend.admin_routes import router as admin_router

# ---------------------------------------------------
# App + CORS
# ---------------------------------------------------
app = FastAPI(title="News API Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# # after app = FastAPI(...) and middleware
# app.include_router(admin_router)


# ... after app and CORS setup
app.include_router(admin_router)


# ---------------------------------------------------
# Singletons
# ---------------------------------------------------
sentiment_analyzer = NewsSentimentEmotionAnalyzer()
ner_analyzer = NewsNerAnalyzer()

# ---------------------------------------------------
# Helpers
# ---------------------------------------------------



from fastapi.openapi.utils import get_openapi

def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    schema = get_openapi(
        title="News API Backend",
        version="1.0.0",
        description="API",
        routes=app.routes,
    )
    # ensure components and securitySchemes exist
    schema.setdefault("components", {}).setdefault("securitySchemes", {}).update({
        "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
    })
    # apply bearer to admin routes by default (optional)
    schema["security"] = [{"bearerAuth": []}]
    app.openapi_schema = schema
    return app.openapi_schema

app.openapi = custom_openapi









def topic_modeling(text: str):
    topics = []
    description = (text or "").lower()
    if "ai" in description or "artificial intelligence" in description:
        topics.append("AI")
    if "finance" in description or "economy" in description:
        topics.append("Finance")
    if "technology" in description or "tech" in description:
        topics.append("Technology")
    return topics if topics else ["General"]

def _parse_dt(value):
    if not value:
        return None
    try:
        return dtparser.parse(value)
    except Exception:
        try:
            return datetime.fromisoformat(value)
        except Exception:
            return None

def _source_str(src):
    if isinstance(src, dict):
        return src.get("name") or str(src)
    return src or ""

def clean_sentiment_output(result: dict):
    if result and "score" in result:
        result["score"] = float(result["score"])
    return result

def clean_entities(entities: List[dict]):
    cleaned = []
    for ent in entities or []:
        ent_clean = {}
        for k, v in (ent or {}).items():
            if isinstance(v, (np.float32, np.float64)):
                ent_clean[k] = float(v)
            else:
                ent_clean[k] = v
        cleaned.append(ent_clean)
    return cleaned

def convert_entities(entities_list):
    def convert_entity(entity):
        return {k: (float(v) if isinstance(v, np.floating) else v) for k, v in entity.items()}
    return [[convert_entity(ent) for ent in entities] for entities in entities_list]

# ---------------------------------------------------
# Routes
# ---------------------------------------------------

# main.py
@app.get("/health")
def health():
    return {"ok": True}




@app.get("/news")
def get_news(query: str = Query(..., description="Search term"),
             language: str = "en",
             page_size: int = 5):
    db = SessionLocal()
    try:
        processed = preprocess_text(query)
        cleaned_query = processed["cleaned"]
        suggestion = processed["suggestion"]

        latest_articles = fetch_news(cleaned_query, language, page_size=page_size)

        results = []
        for article_dict in latest_articles:
            url = article_dict.get("url")
            title = article_dict.get("title") or ""
            desc = article_dict.get("description") or ""
            published_dt = _parse_dt(article_dict.get("publishedAt"))
            src_name = _source_str(article_dict.get("source"))
            img = article_dict.get("urlToImage")

            # News table
            news_article = db.query(News).filter_by(url=url).first()
            if not news_article:
                news_article = News(
                    title=title,
                    description=desc,
                    published_at=published_dt,
                    source=src_name,
                    url=url,
                    image_url=img
                )
                db.add(news_article)
                db.flush()

            # Article table (mirror, keyed by URL)
            article_obj = db.query(Article).filter_by(url=url).first()
            if not article_obj:
                article_obj = Article(
                    title=title,
                    description=desc,
                    url=url,
                    published_at=published_dt,
                    source=src_name
                )
                db.add(article_obj)
                db.flush()

            article_id = article_obj.id

            # Sentiment (idempotent)
            sentiment_result = sentiment_analyzer.analyze_sentiment(desc or title or "")
            sentiment_result = clean_sentiment_output(sentiment_result)
            if not db.query(Sentiment).filter_by(article_id=article_id).first():
                db.add(Sentiment(
                    article_id=article_id,
                    title=title,
                    sentiment=float(sentiment_result.get("score", 0.0)),
                    sentiment_label=sentiment_result.get("label") or "neutral"
                ))

            # Topics mapping
            detected_topics = topic_modeling(desc or title or "")
            for topic_name in detected_topics:
                topic_obj = db.query(Topic).filter_by(name=topic_name).first()
                if not topic_obj:
                    topic_obj = Topic(name=topic_name, description=f"News about {topic_name}")
                    db.add(topic_obj)
                    db.flush()
                if not db.query(ArticleTopic).filter_by(article_id=article_id, topic_id=topic_obj.id).first():
                    db.add(ArticleTopic(article_id=article_id, topic_id=topic_obj.id))

            db.commit()

            results.append({
                "title": title,
                "description": desc,
                "sentiment": sentiment_result,
                "image_url": img,
                "article_id": article_id
            })

        return {
            "original_query": query,
            "cleaned_query": cleaned_query,
            "suggestion": suggestion,
            "results": results
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()

@app.post("/extract_keywords")
def extract_keywords_api(texts: list = Body(...)):
    keywords = extract_keywords_from_texts(texts, top_n=5)
    return {"keywords": keywords}

@app.get("/news/keywords")
def get_keywords_for_latest_news(top_n: int = 5):
    db = SessionLocal()
    try:
        articles = db.query(News).order_by(News.published_at.desc()).limit(20).all()
        article_dicts = [{"title": a.title, "description": a.description} for a in articles]
        keywords_list = extract_keywords(article_dicts, top_n=top_n)
        results = []
        for article, kws in zip(article_dicts, keywords_list):
            results.append({"title": article["title"], "description": article["description"], "keywords": kws})
        return {"results": results}
    finally:
        db.close()

# Auth + profile
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

@app.post("/register")
def register_user_api(request: RegisterRequest):
    success, message = register_user(request.username, request.email, request.password)
    return {"success": success, "message": message}

class LoginRequest(BaseModel):
    identifier: str
    password: str

@app.post("/login")
def login_user_api(request: LoginRequest):
    success, user = login_user(request.identifier, request.password)
    if success:
        return {
            "success": True,
            "username": user.username,
            "email": user.email,
            "language": user.language,
            "interests": user.interests,
        }
    raise HTTPException(status_code=401, detail="Incorrect username/email or password")

@app.get("/user/profile/{username}")
def get_profile(username: str):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return {
            "username": user.username,
            "email": user.email,
            "language": user.language,
            "interests": user.interests
        }
    finally:
        db.close()

class ProfileUpdate(BaseModel):
    email: str
    language: str
    interests: str

@app.put("/user/profile/{username}")
def update_profile(username: str, update: ProfileUpdate):
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.username == username).first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        email_owner = db.query(User).filter(User.email == update.email).first()
        if email_owner and email_owner.id != user.id:
            raise HTTPException(status_code=400, detail="Email already in use by another user")
        user.email = update.email
        user.language = update.language
        user.interests = update.interests
        db.commit()
        return {"success": True, "message": "Profile updated"}
    finally:
        db.close()

# NLP endpoints
@app.post("/analyze_sentiment")
def analyze_sentiment_api(texts: list = Body(...)):
    results = sentiment_analyzer.batch_analyze_sentiment(texts)
    return {"sentiments": results}

@app.post("/extract_entities")
def extract_entities_api(texts: list = Body(...)):
    entities = ner_analyzer.batch_extract_entities(texts)
    entities_converted = convert_entities(entities)
    return {"entities": entities_converted}

@app.post("/analyze")
def analyze(text: str = Form(...)):
    sentiment_result = clean_sentiment_output(sentiment_analyzer.analyze_sentiment(text))
    entities_result = clean_entities(ner_analyzer.extract_entities(text))
    return {"sentiment": sentiment_result, "entities": entities_result}

class BatchAnalyzeRequest(BaseModel):
    articles: List[str]

@app.post("/analyze_batch")
async def analyze_batch(request: BatchAnalyzeRequest):
    texts = request.articles
    sentiments, entities = [], []
    for txt in texts:
        sent = clean_sentiment_output(sentiment_analyzer.analyze_sentiment(txt))
        ents = clean_entities(ner_analyzer.extract_entities(txt))
        sentiments.append(sent)
        entities.append(ents)
    return {"sentiments": sentiments, "entities": entities}

# Analytics for Streamlit
@app.get("/analytics/trend")
def analytics_trend(days: int = 30):
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(days=days)

        points = db.query(
            func.date(Article.published_at).label("date"),
            Topic.name.label("topic"),
            func.count(Article.id).label("topic_count"),
            func.avg(Sentiment.sentiment).label("avg_sentiment")
        ).join(ArticleTopic, ArticleTopic.article_id == Article.id)\
         .join(Topic, Topic.id == ArticleTopic.topic_id)\
         .join(Sentiment, Sentiment.article_id == Article.id)\
         .filter(Article.published_at.isnot(None))\
         .filter(Article.published_at >= since)\
         .group_by(func.date(Article.published_at), Topic.name).all()

        sentiment_dist = dict(
            db.query(Sentiment.sentiment_label, func.count(Sentiment.id))
              .group_by(Sentiment.sentiment_label).all()
        )

        topic_sent = [
            {
                "topic": tname,
                "avg_sentiment": float(avg or 0.0),
                "n": int(n or 0)
            }
            for tname, avg, n in db.query(
                Topic.name,
                func.avg(Sentiment.sentiment),
                func.count(Article.id)
            ).join(ArticleTopic, ArticleTopic.topic_id == Topic.id)
             .join(Article, Article.id == ArticleTopic.article_id)
             .join(Sentiment, Sentiment.article_id == Article.id)
             .group_by(Topic.name).all()
        ]

        return {
            "points": [
                {
                    "date": str(d),
                    "topic": topic,
                    "topic_count": int(cnt or 0),
                    "avg_sentiment": float(avg or 0.0)
                }
                for d, topic, cnt, avg in points
            ],
            "sentiment_distribution": sentiment_dist,
            "topic_sentiment": topic_sent
        }
    finally:
        db.close()

# Topic utilities
class TopicsFromArticlesRequest(BaseModel):
    articles: List[str]
    num_topics: int = 5

@app.post("/topics")
async def extract_topics(request: TopicsFromArticlesRequest):
    try:
        result = get_topics_from_articles(request.articles, request.num_topics)
        return result
    except Exception as e:
        return {"error": str(e)}

class AddTopicsRequest(BaseModel):
    topic_names: List[str]
    article_id: int

@app.post("/add_topics")
def add_topics(request: AddTopicsRequest):
    db = SessionLocal()
    created_topics: List[str] = []
    added_mappings: List[dict] = []
    try:
        article = db.query(Article).filter_by(id=request.article_id).first()
        if not article:
            raise HTTPException(status_code=404, detail=f"Article with id {request.article_id} not found.")
        for name in request.topic_names:
            topic_obj = db.query(Topic).filter_by(name=name).first()
            if not topic_obj:
                topic_obj = Topic(name=name, description=f"News about {name}")
                db.add(topic_obj)
                db.flush()
                created_topics.append(topic_obj.name)
            mapping = db.query(ArticleTopic).filter_by(
                article_id=request.article_id,
                topic_id=topic_obj.id
            ).first()
            if not mapping:
                db.add(ArticleTopic(article_id=request.article_id, topic_id=topic_obj.id))
                added_mappings.append({"topic": name, "article_id": request.article_id})
        db.commit()
        return {
            "status": "success",
            "added_topics": created_topics,
            "added_mappings": added_mappings,
            "article_id": request.article_id
        }
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        db.close()



