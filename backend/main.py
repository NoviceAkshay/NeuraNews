from fastapi import FastAPI, Query, HTTPException, Body, Form
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from backend.database import SessionLocal
from backend.models import User, News
from backend.auth_service import register_user, login_user
from backend.text_cleaning import preprocess_text
from backend.keyword_extractor import preprocess_news, extract_topics, extract_keywords
from backend.news_service import fetch_news
from backend.keyword_extractor import extract_keywords_from_texts
from backend.sentement_analyzer import NewsSentimentEmotionAnalyzer
from backend.ner_analyzer import NewsNerAnalyzer
import numpy as np

from fastapi import Request
from fastapi.responses import JSONResponse




app = FastAPI(title="News API Backend")

# --- CORS for frontend ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Instantiate once to avoid reloading models repeatedly
sentiment_analyzer = NewsSentimentEmotionAnalyzer()
ner_analyzer = NewsNerAnalyzer()


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




sentiment_model = NewsSentimentEmotionAnalyzer()

@app.post("/analyze_sentiment")
def analyze_sentiment_api(texts: list = Body(...)):
    results = sentiment_model.batch_analyze_sentiment(texts)
    return {"sentiments": results}



from backend.ner_analyzer import NewsNerAnalyzer

ner_model = NewsNerAnalyzer()

@app.post("/extract_entities")
def extract_entities_api(texts: list = Body(...)):
    entities = ner_model.batch_extract_entities(texts)
    entities_converted = convert_entities(entities)
    return {"entities": entities_converted}


import numpy as np

def convert_entities(entities_list):
    def convert_entity(entity):
        # Convert all values in the dictionary
        return {k: (float(v) if isinstance(v, np.floating) else v) for k, v in entity.items()}
    return [[convert_entity(ent) for ent in entities] for entities in entities_list]




import numpy as np

def clean_sentiment_output(result):
    if 'score' in result:
        result['score'] = float(result['score'])
    return result

def clean_entities(entities):
    cleaned = []
    for ent in entities:
        ent_clean = ent.copy()
        for k, v in ent_clean.items():
            if isinstance(v, (np.float32, np.float64)):
                ent_clean[k] = float(v)
        cleaned.append(ent_clean)
    return cleaned

@app.post("/analyze_batch")
async def analyze_batch(request: Request):
    payload = await request.json()
    texts = payload if isinstance(payload, list) else payload.get("texts", [])
    sentiments = []
    entities = []
    for txt in texts:
        sent = sentiment_analyzer.analyze_sentiment(txt)
        sent = clean_sentiment_output(sent)
        ents = ner_analyzer.extract_entities(txt)
        ents = clean_entities(ents)
        sentiments.append(sent)
        entities.append(ents)
    return JSONResponse(content={
        "sentiments": sentiments,
        "entities": entities
    })


@app.post("/analyze")
def analyze(text: str = Form(...)):
    sentiment_result = sentiment_analyzer.analyze_sentiment(text)
    sentiment_result = clean_sentiment_output(sentiment_result)

    entities_result = ner_analyzer.extract_entities(text)
    entities_result = clean_entities(entities_result)

    return {
        "sentiment": sentiment_result,
        "entities": entities_result
    }


@app.post("/analyze_batch")
async def analyze_batch(request: Request):
    payload = await request.json()
    texts = payload if isinstance(payload, list) else payload.get("texts", [])
    sentiments = [sentiment_analyzer.analyze_sentiment(txt) for txt in texts]
    entities = [ner_analyzer.extract_entities(txt) for txt in texts]
    return JSONResponse(content={
        "sentiments": sentiments,
        "entities": entities
    })
