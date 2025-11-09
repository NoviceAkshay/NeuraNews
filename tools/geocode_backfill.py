import os, sys
from time import sleep
from geopy.geocoders import Nominatim
from backend.database import SessionLocal
from backend.models import Article

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
geoloc = Nominatim(user_agent="news-geo")

db = SessionLocal()
try:
    rows = (
        db.query(Article)
        .filter(Article.location.isnot(None))
        .filter((Article.lat.is_(None)) | (Article.lon.is_(None)))
        .filter(Article.published_at.isnot(None))         # Only update articles with a timestamp
        .all()
    )

    seen: dict[str, tuple[float | None, float | None]] = {}
    updated = 0
    skipped = 0
    failed_locs = []

    for a in rows:
        loc = (a.location or "").strip()
        if not loc:
            skipped += 1
            continue
        if loc not in seen:
            try:
                r = geoloc.geocode(loc, timeout=10)
                seen[loc] = (r.latitude, r.longitude) if r else (None, None)
                if not r:
                    failed_locs.append(loc)
                sleep(1.1)  # Respect Nominatim rate limit
            except Exception as e:
                print(f"Geocoding failed for location '{loc}': {e}")
                seen[loc] = (None, None)
                failed_locs.append(loc)
        lat, lon = seen[loc]
        if lat is not None and lon is not None:
            a.lat, a.lon = float(lat), float(lon)
            updated += 1
            if updated % 50 == 0:    # Commit in larger batches for speed
                db.commit()
                print(f"Updated {updated} rows...")
    db.commit()
    print(f"Done. Updated {updated} rows, skipped {skipped} empty locations.")
    if failed_locs:
        print("Failed to geocode the following locations:")
        for loc in set(failed_locs):
            print(loc)
finally:
    db.close()
