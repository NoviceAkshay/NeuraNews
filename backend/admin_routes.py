# backend/admin_routes.py
from fastapi import APIRouter, Depends, HTTPException, Body, Header
from sqlalchemy import func, desc, text
from datetime import datetime, timedelta

from .database import SessionLocal
from .models import User, Article, Topic, ArticleTopic, Sentiment
from .auth_service import login_user
from .admin_auth_simple import (
    create_admin_session,
    require_admin_session,
    revoke_admin_session,
)

router = APIRouter(prefix="/admin", tags=["admin"])

@router.get("/health")
def admin_health():
    # Optional DB ping so /docs and UI can confirm DB connectivity
    db = SessionLocal()
    try:
        db.execute(text("SELECT 1"))
        return {"ok": True, "scope": "admin"}
    finally:
        db.close()

@router.post("/login")
def admin_login(payload: dict = Body(...)):
    identifier = payload.get("identifier")
    password = payload.get("password")
    ok, user = login_user(identifier, password)
    if not ok or not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    if not getattr(user, "is_admin", False):
        raise HTTPException(status_code=403, detail="Admin privileges required")
    token = create_admin_session(user.id)
    return {"token": token, "username": user.username, "email": user.email, "is_admin": True}

@router.post("/logout")
def admin_logout(Authorization: str = Header(...)):
    if not Authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=400, detail="Bad Authorization header")
    token = Authorization.split(" ", 1)[1].strip()
    revoke_admin_session(token)
    return {"ok": True}

@router.get("/me")
def admin_me(claims: dict = Depends(require_admin_session)):
    return {"user_id": claims["user_id"], "username": claims["username"]}

@router.get("/users")
def list_users(_claims: dict = Depends(require_admin_session)):
    db = SessionLocal()
    try:
        rows = db.query(User).order_by(User.created_at.desc()).limit(200).all()
        return [
            {
                "id": u.id,
                "username": u.username,
                "email": u.email,
                "is_admin": bool(u.is_admin),
                "created_at": u.created_at.isoformat() if u.created_at else None,
            }
            for u in rows
        ]
    finally:
        db.close()

@router.get("/stats/trend")
def admin_trend(days: int = 30, _claims: dict = Depends(require_admin_session)):
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(days=days)
        points = (
            db.query(
                func.date(Article.published_at).label("date"),
                Topic.name.label("topic"),
                func.count(Article.id).label("topic_count"),
                func.avg(Sentiment.sentiment).label("avg_sentiment"),
            )
            .join(ArticleTopic, ArticleTopic.article_id == Article.id)
            .join(Topic, Topic.id == ArticleTopic.topic_id)
            .join(Sentiment, Sentiment.article_id == Article.id)
            .filter(Article.published_at.isnot(None))
            .filter(Article.published_at >= since)
            .group_by(func.date(Article.published_at), Topic.name)
            .all()
        )

        sentiment_dist = dict(
            db.query(Sentiment.sentiment_label, func.count(Sentiment.id))
              .group_by(Sentiment.sentiment_label)
              .all()
        )

        return {
            "points": [
                {
                    "date": str(d),
                    "topic": topic,
                    "topic_count": int(cnt or 0),
                    "avg_sentiment": float(avg or 0.0),
                }
                for d, topic, cnt, avg in points
            ],
            "sentiment_distribution": sentiment_dist,
        }
    finally:
        db.close()

# NEW: insights badges for dashboard (uses same admin session dependency)
@router.get("/insights")
def admin_insights(days: int = 30, _claims: dict = Depends(require_admin_session)):
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(days=days)

        # Sentiment counts over window
        s_rows = (
            db.query(Sentiment.sentiment_label, func.count(Sentiment.id))
            .join(Article, Article.id == Sentiment.article_id)
            .filter(Article.published_at.isnot(None))
            .filter(Article.published_at >= since)
            .group_by(Sentiment.sentiment_label)
            .all()
        )
        sentiment_counts = {label: int(c) for label, c in s_rows}

        # Topic counts over window
        t_rows = (
            db.query(Topic.name, func.count(ArticleTopic.article_id))
            .join(ArticleTopic, Topic.id == ArticleTopic.topic_id)
            .join(Article, Article.id == ArticleTopic.article_id)
            .filter(Article.published_at.isnot(None))
            .filter(Article.published_at >= since)
            .group_by(Topic.name)
            .all()
        )
        topic_counts = {name: int(c) for name, c in t_rows}

        dominant_sentiment = (
            max(sentiment_counts, key=sentiment_counts.get) if sentiment_counts else None
        )
        hot_topic = max(topic_counts, key=topic_counts.get) if topic_counts else None

        return {
            "window_days": days,
            "dominant_sentiment": dominant_sentiment,
            "hot_topic": hot_topic,
            "sentiment_counts": sentiment_counts,
            "topic_counts": topic_counts,
        }
    finally:
        db.close()

# NEW: sorted top-topic summary for list in UI
@router.get("/topics/summary")
def admin_topics_summary(
    days: int = 30,
    limit: int = 10,
    _claims: dict = Depends(require_admin_session),
):
    db = SessionLocal()
    try:
        since = datetime.utcnow() - timedelta(days=days)
        rows = (
            db.query(Topic.name, func.count(ArticleTopic.article_id).label("cnt"))
            .join(ArticleTopic, Topic.id == ArticleTopic.topic_id)
            .join(Article, Article.id == ArticleTopic.article_id)
            .filter(Article.published_at.isnot(None))
            .filter(Article.published_at >= since)
            .group_by(Topic.name)
            .order_by(desc("cnt"))
            .limit(limit)
            .all()
        )
        return [{"topic": name, "count": int(cnt)} for name, cnt in rows]
    finally:
        db.close()
    