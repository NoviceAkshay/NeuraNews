import requests
from datetime import datetime, timezone
from .config import NEWS_API_KEY, BASE_URL
from .database import SessionLocal
from .models import News

def make_aware(dt):
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt



def fetch_news(query: str, language: str = "en", page_size: int = 5):
    # Added sortBy=publishedAt to get latest news first
    url = f"{BASE_URL}?q={query}&language={language}&pageSize={page_size}&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
    print(f"Fetching news from URL: {url}")  # Debug print of request URL
    response = requests.get(url)

    if response.status_code != 200:
        print(f"Error fetching news: {response.status_code} - {response.text}")  # Debug error
        return {"error": f"Error fetching news: {response.status_code}"}

    news_data = response.json()
    articles = news_data.get("articles", [])
    print(f"Fetched {len(articles)} articles")  # Print count of fetched articles

    # Print title and description of first few articles to inspect content presence
    for i, article in enumerate(articles[:3]):
        print(f" Article {i + 1} published at: {article.get('publishedAt')}")
        print(f" Article {i + 1} title: {article.get('title')}")
        print(f" Article {i + 1} description: {article.get('description')}")

    results = []
    db = SessionLocal()

    for article in articles:
        published_at = article.get("publishedAt")
        if published_at:
            published_at = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
            published_at = make_aware(published_at)

        news_item = News(
            title=article.get("title", "No title"),
            source=article["source"].get("name", "Unknown"),
            published_at=published_at,
            url=article.get("url", "#"),
            description=article.get("description", "No description"),  # Store description
            image_url=article.get("urlToImage")
        )

        # Check for existing article by URL before inserting
        if not db.query(News).filter(News.url == news_item.url).first():
            db.add(news_item)
            db.commit()

        results.append({
            "title": news_item.title,
            "source": news_item.source,
            "publishedAt": news_item.published_at,
            "url": news_item.url,
            "description": news_item.description,
            "image": news_item.image_url
        })

    db.close()
    print(f"Stored {len(results)} articles from NewsAPI")
    return results
