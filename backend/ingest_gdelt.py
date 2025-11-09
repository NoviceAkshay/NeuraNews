# backend/ingest_gdelt.py
from datetime import datetime
from dateutil import parser
from backend.gdelt_client import fetch_docs
from backend.database import SessionLocal
from backend.models import Article

def parse_gdelt_datetime(s: str):
    if not s:
        return None
    s = s.strip()
    # Try generic ISO/textual parsing first
    try:
        return parser.parse(s)
    except Exception:
        pass
    # Handle compact numeric formats sometimes used in feeds (YYYYMMDD[HH[MM[SS]]])
    try:
        if s.isdigit():
            if len(s) == 8:
                return datetime.strptime(s, "%Y%m%d")
            if len(s) == 12:
                return datetime.strptime(s, "%Y%m%d%H%M")
            if len(s) == 14:
                return datetime.strptime(s, "%Y%m%d%H%M%S")
    except Exception:
        return None
    return None

def upsert_gdelt(hours=24, query=None, max_records=150):
    # Ensure query uses DOC 2.0 rules: non-empty and OR groups in parentheses
    # e.g., "(AI OR climate OR india)"
    docs = fetch_docs(hours=hours, query=query, max_records=max_records)
    db = SessionLocal()
    inserted = 0
    try:
        for d in docs:
            url = d.get("url")
            if not url:
                continue

            row = db.query(Article).filter(Article.url == url).first()
            if row:
                # backfill geo if the new payload has coordinates
                if (row.lat is None or row.lon is None) and d.get("lat") and d.get("lon"):
                    row.lat, row.lon = d["lat"], d["lon"]
                # set location if missing (e.g., country name from DOC sourcecountry)
                if d.get("location") and not row.location:
                    row.location = d["location"]
                # backfill published_at if missing
                if not row.published_at:
                    raw = d.get("published_at")
                    row.published_at = parse_gdelt_datetime(raw) or datetime.utcnow()
                continue

            raw_ts = d.get("published_at")
            published = parse_gdelt_datetime(raw_ts) or datetime.utcnow()

            db.add(Article(
                title=d.get("title") or "(untitled)",
                body=None,                      # hydrate later if you fetch fulltext
                published_at=published,         # never NULL so it passes window filters
                source=d.get("source"),
                url=url,
                location=d.get("location"),     # country fallback mapped in gdelt_client
                lat=d.get("lat"),
                lon=d.get("lon"),
                description=None,
            ))
            inserted += 1

        db.commit()
        print(f"Inserted {inserted} GDELT articles.")
    finally:
        db.close()

if __name__ == "__main__":
    # Parenthesized OR group is required by DOC 2.0 query syntax
    upsert_gdelt(hours=168, query="(AI OR climate OR india)", max_records=150)
