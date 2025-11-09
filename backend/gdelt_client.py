# backend/gdelt_client.py
import requests

BASE = "https://api.gdeltproject.org/api/v2/doc/doc"

# Minimal ISO2 -> country name map (extend as needed)
ISO2_TO_COUNTRY = {
    "IN": "India",
    "US": "United States",
    "GB": "United Kingdom",
    "CA": "Canada",
    "AU": "Australia",
    "DE": "Germany",
    "FR": "France",
    "BR": "Brazil",
    "JP": "Japan",
    "CN": "China",
    "RU": "Russia",
    "ZA": "South Africa",
}

def fetch_docs(hours=24, query="india", max_records=150, use_jsonfeed=False):
    params = {
        "format": "JSONFeed" if use_jsonfeed else "JSON",
        "timespan": f"{hours}h",
        "maxrecords": max_records,
        "mode": "ArtList",
        "sort": "DateDesc",
        "query": query,  # must be non-empty
    }
    r = requests.get(BASE, params=params, headers={"User-Agent": "appnews/1.0"}, timeout=30)
    print("GDELT URL:", r.url, "HTTP", r.status_code)
    if r.status_code != 200:
        print("Body:", r.text[:200])
        return []
    try:
        data = r.json()
    except Exception:
        print("Non-JSON body:", r.text[:200])
        return []

    arts = data.get("articles") or data.get("documents") or []
    print("Articles fetched:", len(arts))

    out = []
    for a in arts:
        # country fallback from DOC 2.0; map ISO2 -> country name for geocoding
        code = (a.get("sourcecountry") or "").upper()
        place = ISO2_TO_COUNTRY.get(code) or code  # fall back to ISO code if unmapped

        out.append({
            "title": a.get("title"),
            "url": a.get("url"),
            "published_at": a.get("seendate") or a.get("date"),
            "source": a.get("domain"),
            "location": place,   # string to geocode later
            "lat": None,         # leave empty; backfill will set centroids
            "lon": None,
        })
    return out
