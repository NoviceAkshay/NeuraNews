from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.database import SessionLocal
from backend.models import User, News
from backend.auth_service import register_user, login_user
from backend.text_cleaning import preprocess_text
from backend.keyword_extractor import preprocess_news, extract_topics, extract_keywords
from backend.news_service import fetch_news
from backend.keyword_extractor import extract_keywords_from_texts

app = FastAPI(title="News API Backend")

# --- CORS for frontend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- News Fetch API ---
@app.get("/news")
def get_news(query: str = Query(..., description="Search term"),
             language: str = "en",
             page_size: int = 5):

    processed = preprocess_text(query)
    cleaned_query = processed["cleaned"]
    suggestion = processed["suggestion"]

    # Fetch CURRENT news from NewsAPI.org and store to DB
    latest_articles = fetch_news(cleaned_query, language, page_size=page_size)

    return {
        "original_query": query,
        "cleaned_query": cleaned_query,
        "suggestion": suggestion,
        "results": latest_articles
    }

# --- Keyword Extraction API from raw texts ---


@app.post("/extract_keywords")
def extract_keywords_api(texts: list = Body(...)):
    keywords = extract_keywords_from_texts(texts, top_n=5)
    return {"keywords": keywords}

# --- Keyword Extraction from Latest News in DB ---
@app.get("/news/keywords")
def get_keywords_for_latest_news(top_n: int = 5):
    db = SessionLocal()
    try:
        articles = db.query(News).order_by(News.published_at.desc()).limit(20).all()
        article_dicts = [{'title': a.title, 'description': a.description} for a in articles]

        keywords_list = extract_keywords(article_dicts, top_n=top_n)

        results = []
        for article, keywords in zip(article_dicts, keywords_list):
            results.append({
                "title": article['title'],
                "description": article['description'],
                "keywords": keywords
            })
        return {"results": results}
    finally:
        db.close()

# --- Registration API ---
class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str

@app.post("/register")
def register_user_api(request: RegisterRequest):
    success, message = register_user(request.username, request.email, request.password)
    return {"success": success, "message": message}

# --- Login API ---
class LoginRequest(BaseModel):
    identifier: str  # Username or Email
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
    else:
        raise HTTPException(status_code=401, detail="Incorrect username/email or password")

# --- User Profile GET/PUT ---

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
