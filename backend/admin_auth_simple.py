# backend/admin_auth_simple.py
import secrets
from datetime import datetime, timedelta
from fastapi import HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional

from .database import SessionLocal
from .models import AdminSession, User

SESSION_TTL_MINUTES = 120  # change via env if desired

def _now_utc():
    return datetime.utcnow()

def create_admin_session(user_id: int) -> str:
    token = secrets.token_urlsafe(48)
    db: Session = SessionLocal()
    try:
        expires = _now_utc() + timedelta(minutes=SESSION_TTL_MINUTES)
        sess = AdminSession(token=token, user_id=user_id, expires_at=expires)
        db.add(sess)
        db.commit()
        return token
    finally:
        db.close()

def get_session(token: str) -> Optional[AdminSession]:
    db: Session = SessionLocal()
    try:
        sess = db.query(AdminSession).filter(AdminSession.token == token).first()
        return sess
    finally:
        db.close()

def require_admin_session(Authorization: Optional[str] = Header(default=None)) -> dict:
    if not Authorization or not Authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing bearer token")
    token = Authorization.split(" ", 1)[1].strip()
    sess = get_session(token)
    if not sess:
        raise HTTPException(status_code=401, detail="Invalid admin session")
    if sess.expires_at <= _now_utc():
        raise HTTPException(status_code=401, detail="Admin session expired")
    # Optional: verify user still admin
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == sess.user_id).first()
        if not user or not user.is_admin:
            raise HTTPException(status_code=403, detail="Admin privileges revoked")
        return {"user_id": user.id, "username": user.username}
    finally:
        db.close()

def revoke_admin_session(token: str):
    db = SessionLocal()
    try:
        db.query(AdminSession).filter(AdminSession.token == token).delete()
        db.commit()
    finally:
        db.close()
