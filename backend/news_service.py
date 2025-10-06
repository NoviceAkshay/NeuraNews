
# -----------------------------------------------------------------------------------------------------------------------------------------------------------
#                                                     *****     News fetching logic     *****
# -----------------------------------------------------------------------------------------------------------------------------------------------------------



import requests
from .config import NEWS_API_KEY, BASE_URL
from .database import SessionLocal
from .models import News
from datetime import datetime

def fetch_news(query: str, language: str = "en", page_size: int = 5):
    """
    Fetch news from NewsAPI and store in PostgreSQL.
    """
    url = f"{BASE_URL}?q={query}&language={language}&pageSize={page_size}&apiKey={NEWS_API_KEY}"
    response = requests.get(url)

    if response.status_code != 200:
        return {"error": f"Error fetching news: {response.status_code}"}

    news_data = response.json()
    articles = news_data.get("articles", [])

    results = []
    db = SessionLocal()

    for article in articles:
        # Convert publishedAt to datetime
        published_at = article.get("publishedAt")
        if published_at:
            published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))

        # Create News object
        news_item = News(
            title=article.get("title", "No title"),
            source=article["source"].get("name", "Unknown"),
            published_at=published_at,
            url=article.get("url", "#"),
            description=article.get("description", "No description"),
            image_url=article.get("urlToImage")
        )

        # Save to DB if URL not already exists
        if not db.query(News).filter(News.url == news_item.url).first():
            db.add(news_item)
            db.commit()

        # Add to results for API response
        results.append({
            "title": news_item.title,
            "source": news_item.source,
            "publishedAt": news_item.published_at,
            "url": news_item.url,
            "description": news_item.description,
            "image": news_item.image_url
        })

    db.close()
    return results

