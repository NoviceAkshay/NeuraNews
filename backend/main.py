# -----------------------------------------------------------------------------------------------------------------------------------------------------------
#                                                     *****     FastAPI entry point     *****
# -----------------------------------------------------------------------------------------------------------------------------------------------------------


from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from .news_service import fetch_news
from .text_cleaning import preprocess_text   # <-- import text cleaning

app = FastAPI(title="News API Backend")

# Allow frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/news")
def get_news(
    query: str = Query(..., description="Search term"),
    language: str = "en",
    page_size: int = 5
):
    # Preprocess the user query
    processed = preprocess_text(query)
    cleaned_query = processed["cleaned"]
    suggestion = processed["suggestion"]

    # Fetch news using the cleaned query
    results = fetch_news(cleaned_query, language, page_size)

    return {
        "original_query": query,
        "cleaned_query": cleaned_query,
        "suggestion": suggestion,
        "results": results
    }
