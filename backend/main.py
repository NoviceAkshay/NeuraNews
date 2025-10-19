from fastapi import FastAPI, Query, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.database import SessionLocal
from backend.models import User
from backend.auth_service import register_user, login_user
from backend.text_cleaning import preprocess_text
from backend.keyword_extractor import preprocess_news, extract_topics, extract_keywords
from backend.news_service import fetch_news





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

    # Return ONLY the just-fetched articles for this query (not the DB cache)
    # Ensure frontend gets up-to-date results, every time they search

    return {
        "original_query": query,
        "cleaned_query": cleaned_query,
        "suggestion": suggestion,
        "results": latest_articles  # These are structured for frontend display
    }


# --- Keyword Extraction API ---
@app.post("/extract_keywords")
def extract_keywords_api(texts: list = Body(...)):
    keywords = extract_keywords(texts, min_n=3, max_n=5)
    return {"keywords": keywords}

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

# GET Profile
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

# PUT Profile (Full Edit)
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

        # Check if email belongs to a different user
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

# -----------------------------------------------------------------------------
# Add any additional endpoints as needed (analytics, etc)
# -----------------------------------------------------------------------------
