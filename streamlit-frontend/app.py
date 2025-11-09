
import os
import sys
import re
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt  # preserved (unused)
import speech_recognition as sr
from streamlit_mic_recorder import speech_to_text  # preserved (unused)

# Optional insights import (kept from your original)
from trend_insights import run_trend_insights

# --- API base (secrets -> env -> default). Keep only this; do NOT override later. ---
def _get_api_base():
    try:
        return st.secrets["API_BASE"]              # secrets.toml
    except Exception:
        return os.getenv("API_BASE", "http://127.0.0.1:8000")  # env or default

API_BASE = _get_api_base()

# --- Safe import for Time Series page (surface real error if import fails) ---
run_time_series_error = None
try:
    from time_series import run as run_time_series   # streamlit-frontend/time_series.py
except Exception as e:
    run_time_series = None
    run_time_series_error = str(e)


try:
    from geo_map import run as run_geo_map
    run_geo_map_error = None
except Exception as e:
    run_geo_map = None
    run_geo_map_error = str(e)


# ----------------------------------------------------------------------------
# Backend health
# ----------------------------------------------------------------------------
def backend_ok() -> bool:
    """Check backend health endpoint."""
    try:
        r = requests.get(f"{API_BASE}/health", timeout=3)
        return r.status_code == 200 and r.json().get("ok") is True
    except Exception:
        return False


# ----------------------------------------------------------------------------
# Fetch helpers (deduplicated)
# ----------------------------------------------------------------------------
def fetch_trend(days: int = 30):
    """Fetch trend analytics data; return None on error."""
    try:
        r = requests.get(f"{API_BASE}/analytics/trend", params={"days": days}, timeout=15)
        if r.status_code != 200:
            # Show backend message if present to aid debugging
            try:
                detail = r.json()
            except Exception:
                detail = r.text
            st.error(f"Backend error {r.status_code}: {detail}")
            return None
        return r.json()
    except Exception as e:
        st.error(f"Request failed: {e}")
        return None


def fetch_latest_news(query="technology", language="en", page_size=10):
    """Fetch latest news from backend /news endpoint."""
    try:
        r = requests.get(
            f"{API_BASE}/news",
            params={"query": query, "language": language, "page_size": page_size},
            timeout=60,
        )
        if r.status_code != 200:
            try:
                detail = r.json()
            except Exception:
                detail = r.text
            st.error(f"Failed to fetch news: {r.status_code} - {detail}")
            return None
        return r.json()
    except Exception as e:
        st.error(f"Failed to fetch news: {e}")
        return None


def prepare_trend_data(news_items, sentiment_list, topics, doc_topic_map):
    """Prepare a lightweight DataFrame for trend insights if needed."""
    rows = []
    for idx, article in enumerate(news_items):
        sentiment = sentiment_list[idx] if idx < len(sentiment_list) else {}
        topic_info = doc_topic_map.get(idx, {})
        rows.append(
            {
                "title": article.get("title"),
                "sentiment": sentiment.get("score", 0),
                "topic1_count": topic_info.get("count", 0),
                "published_at": article.get("publishedAt"),
            }
        )
    return pd.DataFrame(rows)


def get_image_url(article: dict) -> str:
    # Try common keys first
    for k in ["image", "image_url", "urlToImage", "thumbnail", "url_image", "banner"]:
        url = (article or {}).get(k)
        if isinstance(url, str) and url.strip().lower().startswith(("http://", "https://")):
            return url.strip()
    return ""



def get_image_url(article: dict) -> str:
    for k in ["image", "image_url", "urlToImage", "thumbnail", "url_image", "banner"]:
        url = (article or {}).get(k)
        if isinstance(url, str) and url.strip().lower().startswith(("http://", "https://")):
            return url.strip()
    return ""




# add this helper somewhere near other page helpers
def nav_sidebar():
    st.sidebar.title("Navigation")
    choice = st.sidebar.radio(
        "Go to",
        ["Landing", "Explore", "Admin", "Trend Insights", "Time Series"],
        index=["Landing", "Explore", "Admin", "Trend Insights", "Time Series"].index(
            st.session_state.get("page", "landing").title().replace("_", " ")
        )
        if isinstance(st.session_state.get("page"), str) else 0,
    )
    st.session_state["page"] = choice.lower().replace(" ", "_")




# ----------------------------------------------------------------------------
# Safe rerun wrapper (consistent across app)
# ----------------------------------------------------------------------------
def safe_rerun():
    """Trigger a rerun safely across Streamlit versions."""
    if hasattr(st, "experimental_rerun"):
        try:
            st.experimental_rerun()
            return
        except Exception:
            pass
    if hasattr(st, "rerun"):
        try:
            st.rerun()
            return
        except Exception:
            pass
    st.session_state["_force_refresh"] = st.session_state.get("_force_refresh", 0) + 1


# ----------------------------------------------------------------------------
# Session initialization (mirror legacy and new keys for compatibility)
# ----------------------------------------------------------------------------
initial_keys = [
    ("cachednews", []),
    ("cached_articles", []),
    ("cachedsentiments", []),
    ("cached_sentiments", []),
    ("cachedtopics", []),
    ("cached_topics", []),
    ("cacheddoctopics", {}),
    ("cached_doc_topics", {}),
    ("cachedkeywords", []),
    ("cached_keywords", []),
    ("cachedentities", []),
    ("cached_entities", []),
    ("cachedquery", ""),
    ("cached_query", ""),
    ("cachedlang", "en"),
    ("cached_lang", "en"),
    ("last_query", "technology"),
    ("loggedin", False),
    ("logged_in", False),
    ("username", ""),
    ("page", "landing"),
    ("selectedarticle", None),
    ("selected_article", None),
]
for key, default in initial_keys:
    if key not in st.session_state:
        st.session_state[key] = default

# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Neura News",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ensure import path for backend.auth_service
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.auth_service import register_user, login_user  # noqa: E402

BACKEND_URL = "http://127.0.0.1:8000/news"  # preserved


# ----------------------------------------------------------------------------
# CSS - Unified Modern Design
# ----------------------------------------------------------------------------
st.markdown(
    """
<style>
    :root {
        --primary: #1a1a1a;
        --secondary: #2c2c2c;
        --accent: #4a90e2;
        --foreground: #242423;
        --background: #fafbf8;
        --card: #f5f1e8;
        --border: #e8e3d8;
    }
    .glass {
        background: rgba(255, 255, 255, 0.15);
        backdrop-filter: blur(10px);
        border-radius: 24px;
        border: 1px solid rgba(255, 255, 255, 0.2);
        padding: 1.5rem;
    }
    .newspaper-masthead {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        border-top: 3px solid var(--foreground);
        border-bottom: 3px solid var(--foreground);
        padding: 1rem 0;
        margin-bottom: 2rem;
        letter-spacing: 2px;
    }
    .feature-card {
        background: var(--card);
        border-radius: 20px;
        padding: 1rem;
        box-shadow: 0 0 15px 2px rgba(74, 144, 226, 0.2);
        margin-bottom: 1rem;
        text-align: center;
    }
    .button-custom {
        font-weight: 600;
        background-color: var(--accent);
        color: white;
        padding: 0.75rem 1.5rem;
        border: none;
        border-radius: 10px;
        cursor: pointer;
        margin-top: 1rem;
        width: 100%;
    }
    .button-custom:hover {
        background-color: #3a78d6;
    }
    .analytics-section {
        background: #ffffff;
        border-radius: 12px;
        padding: 20px;
        margin-top: 20px;
        box-shadow: 0 2px 12px rgba(0,0,0,0.08);
    }
    .analytics-title {
        font-size: 1.3rem;
        font-weight: 600;
        color: #242423;
        margin-bottom: 15px;
        border-bottom: 2px solid #4a90e2;
        padding-bottom: 8px;
    }
    .keyword-tag {
        display: inline-block;
        background: #4a90e220;
        color: #2c5282;
        padding: 6px 12px;
        border-radius: 8px;
        margin: 4px;
        font-size: 14px;
        font-weight: 500;
    }
    .entity-tag {
        display: inline-block;
        background: #c2c3c470;
        color: #747374;
        padding: 6px 12px;
        border-radius: 8px;
        margin: 4px;
        font-size: 13px;
    }
    .entity-type {
        color: #565657;
        font-size: 11px;
        font-weight: 600;
    }
    .sentiment-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        margin: 15px 0;
    }
    .sentiment-emoji {
        font-size: 3rem;
        margin-bottom: 10px;
    }
    .article-detail-card {
        background: #fafbf8;
        border-radius: 15px;
        padding: 30px;
        box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        margin-bottom: 30px;
    }
    .article-image-large {
        width: 100%;
        max-height: 400px;
        object-fit: cover;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    .article-title-large {
        font-size: 2rem;
        font-weight: 700;
        color: #242423;
        margin-bottom: 15px;
        line-height: 1.3;
    }
    .article-meta {
        color: #747374;
        font-size: 0.95rem;
        margin-bottom: 20px;
    }
    .article-description-full {
        font-size: 1.1rem;
        line-height: 1.8;
        color: #242423;
        margin-bottom: 25px;
    }
    .open-article-btn {
        display: inline-block;
        background: #4a90e2;
        color: white;
        padding: 12px 24px;
        border-radius: 8px;
        text-decoration: none;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .open-article-btn:hover {
        background: #3a78d6;
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(74, 144, 226, 0.4);
    }
</style>
""",
    unsafe_allow_html=True,
)

# ----------------------------------------------------------------------------
# Utility
# ----------------------------------------------------------------------------
def is_valid_email(email: str) -> bool:
    """Basic email validator."""
    return re.match(r"[^@]+@[^@]+\.[^@]+", email) is not None




# # streamlit-frontend/app.py
# from pathlib import Path
# import sys
#
# APP_DIR = Path(__file__).parent
# if str(APP_DIR) not in sys.path:
#     sys.path.insert(0, str(APP_DIR))  # ensure ./ is importable for sibling modules
#
# run_time_series_error = None
# try:
#     from time_series import run as run_time_series  # sibling module: streamlit-frontend/time_series.py
# except Exception as e:
#     run_time_series = None
#     run_time_series_error = str(e)  # keep the reason visible in UI
#




# ----------------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------------

# --- Session keys ---
extra_keys = [("admin_token", ""), ("admin_user", {})]
for k, v in extra_keys:
    if k not in st.session_state:
        st.session_state[k] = v

# --- Small helpers for admin API calls ---
def admin_api_get(path: str):
    tok = st.session_state.get("admin_token", "")
    headers = {"Authorization": f"Bearer {tok}"} if tok else {}
    r = requests.get(f"{API_BASE}{path}", headers=headers, timeout=60)
    if r.status_code != 200:
        try:
            st.error(f"{path} -> {r.status_code}: {r.json()}")
        except Exception:
            st.error(f"{path} -> {r.status_code}: {r.text}")
        return None
    return r.json()

def admin_api_post(path: str, json=None):
    tok = st.session_state.get("admin_token", "")
    headers = {"Authorization": f"Bearer {tok}"} if tok else {}
    r = requests.post(f"{API_BASE}{path}", json=json, headers=headers, timeout=60)
    if r.status_code != 200:
        try:
            st.error(f"{path} -> {r.status_code}: {r.json()}")
        except Exception:
            st.error(f"{path} -> {r.status_code}: {r.text}")
        return None
    return r.json()

def landing_page():
    """Public landing page with CTAs to login/register."""
    st.markdown('<div class="newspaper-masthead">📰 Neura News</div>', unsafe_allow_html=True)
    st.write(
        """
        Welcome to Neura News — your AI-powered news aggregator.
        Stay informed with the latest headlines, sentiment insights,
        and keyword extraction from global news sources.
        """
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="feature-card">🔎 Search personalized news with filters</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="feature-card">💬 Analyze sentiment & entities in any text</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="feature-card">🎙️ Voice-enabled search and interaction</div>', unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("👤 Login", key="landing_login"):
            st.session_state.page = "login"
            safe_rerun()

    with c2:
        if st.button("📝 Register", key="landing_register"):
            st.session_state.page = "register"
            safe_rerun()

    with c3:
        if st.button("🛡️ Admin Login"):
            st.session_state.page = "admin_login"
            safe_rerun()

    st.markdown("---")

    st.subheader("How Neura News Works")
    st.write(
        """
    - **Real-time News Aggregation:** Collects articles from trusted global sources to keep you updated.
    - **AI-Powered Insights:** Identifies sentiment and key entities in news to give deeper context.
    - **Customizable Searches:** Filter news by language, topic, and volume to get exactly what interests you.
    - **Voice Search:** Conveniently search news hands-free using voice input.
    - **User Profiles:** Save preferences, receive personalized recommendations, and manage your interests.
    """
    )

    st.markdown("---")

    st.subheader("Why Neura News?")
    st.write(
        """
    - **Accurate & Up-to-Date:** Powered by advanced AI and fast backend APIs.
    - **User Friendly:** Clean, modern, and intuitive interface designed for all users.
    - **Secure:** Robust authentication keeps your account and preferences private.
    - **Transparent:** Ethical news sourcing and analysis to keep you well-informed.
    """
    )

    st.markdown("---")

    st.subheader("About")
    st.write(
        """
    Neura News is built with Streamlit and backed by powerful AI services.
    It provides detailed sentiment insights, keyword extraction, and a seamless news reading experience.
    \nExplore the latest trends and stories with confidence and ease.
    """
    )

    st.markdown("---")

    st.subheader("Get Started")
    st.write(
        """
    Join thousands of users staying ahead with Neura News. Whether you want quick updates or in-depth analysis,
    this platform simplifies your news experience with AI-enhanced features.
    """
    )




# --- New: Admin Login page ---
def admin_login_page():
    st.markdown('<div class="newspaper-masthead">🛡️ Admin Login</div>', unsafe_allow_html=True)
    identifier = st.text_input("Admin username or email")
    password = st.text_input("Admin password", type="password")
    if st.button("Login as Admin", use_container_width=True):
        r = requests.post(f"{API_BASE}/admin/login", json={"identifier": identifier, "password": password}, timeout=60)
        if r.status_code == 200:
            data = r.json()
            st.session_state.admin_token = data.get("token", "")
            st.session_state.admin_user = {"username": data.get("username"), "email": data.get("email")}
            st.session_state.page = "admin_dashboard"
            st.success("Admin login successful.")
            safe_rerun()
        else:
            try:
                st.error(f"Login failed: {r.status_code} - {r.json()}")
            except Exception:
                st.error(f"Login failed: {r.status_code} - {r.text}")

    if st.button("⬅ Back to Landing"):
        st.session_state.page = "landing"
        safe_rerun()

# --- New: Admin Dashboard page (guarded) ---
def admin_dashboard_page():
    token = st.session_state.get("admin_token", "")
    if not token:
        st.info("Please login as admin.")
        st.session_state.page = "admin_login"
        safe_rerun()
        return

    st.title("Admin Dashboard")
    with st.sidebar:
        st.success(f"Admin: {st.session_state.get('admin_user',{}).get('username','unknown')}")
        if st.button("Logout Admin"):
            admin_api_post("/admin/logout")
            st.session_state.admin_token = ""
            st.session_state.admin_user = {}
            st.session_state.page = "landing"
            safe_rerun()

    # Basic stats
    data = admin_api_get("/admin/stats/trend?days=30")
    if data:
        st.subheader("Sentiment distribution")
        sd = data.get("sentiment_distribution", {})
        if sd:
            import pandas as pd
            st.bar_chart(pd.Series(sd))

    st.subheader("Users")
    users = admin_api_get("/admin/users")
    if users:
        import pandas as pd
        st.dataframe(pd.DataFrame(users))





def login_page():
    """Login page; sets session flags and routes to dashboard on success."""
    st.markdown('<div class="newspaper-masthead">🔐 Login</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        identifier = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")
        if st.button("🔓 Login", use_container_width=True):
            success, user = login_user(identifier, password)
            if success:
                # Normalize auth flags and page (mirror legacy/new keys)
                st.session_state.logged_in = True
                st.session_state.loggedin = True
                st.session_state.username = user.username
                st.session_state.page = "news_dashboard"
                st.success(f"Welcome, {user.username}!")
                safe_rerun()
            else:
                st.error("Incorrect username/email or password")

        if st.button("📝 Go to Registration", use_container_width=True):
            st.session_state.page = "register"
            safe_rerun()


def register_page():
    """Registration page."""
    st.markdown('<div class="newspaper-masthead">📝 Register</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")
        if st.button("✅ Register", use_container_width=True):
            if not username or not password or not confirm or not email:
                st.warning("All fields required")
            elif password != confirm:
                st.warning("Passwords do not match")
            elif not is_valid_email(email):
                st.warning("Invalid email format")
            else:
                success, msg = register_user(username, email, password)
                if success:
                    st.success(msg)
                    st.info("You can now log in.")
                    st.session_state.page = "login"
                    safe_rerun()
                else:
                    st.error(msg)


def article_analytics_page():
    """Detailed per-article analytics: keywords, sentiment, entities, topics."""
    st.markdown('<div class="newspaper-masthead">📊 Article Analytics</div>', unsafe_allow_html=True)

    def go_back_to_dashboard():
        st.session_state.page = "news_dashboard"
        st.session_state.selected_article = None

    st.button("⬅ Back to Dashboard", key="back_to_dashboard_top", on_click=go_back_to_dashboard)

    article = st.session_state.get("selected_article", {})

    if not article:
        st.error("No article selected")
        return

    # Article Detail Card
    st.markdown('<div class="article-detail-card">', unsafe_allow_html=True)

    # Image
    image_url = article.get("image") or article.get("image_url") or article.get("urlToImage") or ""
    if image_url:
        st.markdown(f'<img src="{image_url}" class="article-image-large"/>', unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="text-align:center;font-size:5rem;padding:60px;background:#c2c3c4;border-radius:12px;margin-bottom:20px;">📰</div>',
            unsafe_allow_html=True,
        )

    # Title
    title = article.get("title", "No Title")
    st.markdown(f'<h1 class="article-title-large">{title}</h1>', unsafe_allow_html=True)

    # Meta information
    source = article.get("source", "Unknown")
    published = article.get("publishedAt", "N/A")
    if published != "N/A":
        try:
            from dateutil import parser

            dt = parser.parse(published)
            published = dt.strftime("%B %d, %Y at %H:%M")
        except Exception:
            pass

    st.markdown(
        f'<p class="article-meta">🏷️ <strong>{source}</strong> &nbsp;|&nbsp; 📅 {published}</p>',
        unsafe_allow_html=True,
    )

    # Description/Full text
    description = article.get("description", "No description available")
    st.markdown(f'<p class="article-description-full">{description}</p>', unsafe_allow_html=True)

    # Open article button
    url = article.get("url", "#")
    st.markdown(f'<a href="{url}" target="_blank" class="open-article-btn">🔗 Open Full Article</a>', unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # Analytics Section
    st.markdown("---")
    st.markdown('<h2 style="text-align:center;color:#242423;margin:30px 0;">📈 Detailed Analytics</h2>', unsafe_allow_html=True)

    # Prepare text for analysis
    analysis_text = (article.get("title", "") + " " + str(article.get("description", "")))

    with st.spinner("🔄 Analyzing article..."):
        keywords = []
        sentiment = {}
        entities = []
        topics = {}

        # Keywords Extraction
        try:
            resp = requests.post(f"{API_BASE}/extract_keywords", json=[analysis_text])
            if resp.status_code == 200:
                keywords = resp.json().get("keywords", [[]])[0]
        except Exception as e:
            st.warning(f"Keywords extraction failed: {e}")

        # Sentiment & Entity Analysis
        try:
            resp = requests.post(f"{API_BASE}/analyze", data={"text": analysis_text})
            if resp.status_code == 200:
                result = resp.json()
                sentiment = result.get("sentiment", {})
                entities = result.get("entities", [])
        except Exception as e:
            st.warning(f"Sentiment/Entity analysis failed: {e}")

        # Topic Modeling
        try:
            resp = requests.post(
                f"{API_BASE}/topics",
                json={"articles": [analysis_text], "num_topics": 3},
            )
            if resp.status_code == 200:
                topics = resp.json()
        except Exception as e:
            st.warning(f"Topic modeling failed: {e}")

    col1, col2 = st.columns(2)

    with col1:
        # Keywords Section
        st.markdown('<div class="analytics-section">', unsafe_allow_html=True)
        st.markdown('<div class="analytics-title">🔑 Keywords</div>', unsafe_allow_html=True)
        if keywords:
            keywords_html = "".join([f'<span class="keyword-tag">{k}</span>' for k in keywords])
            st.markdown(keywords_html, unsafe_allow_html=True)
        else:
            st.info("No keywords detected")
        st.markdown("</div>", unsafe_allow_html=True)

        # Topic Modeling Section
        st.markdown('<div class="analytics-section">', unsafe_allow_html=True)
        st.markdown('<div class="analytics-title">📝 Topics</div>', unsafe_allow_html=True)
        topic_list = topics.get("topics", [])
        if topic_list:
            for topic in topic_list:
                st.markdown(
                    f'<div class="topic-tag"><strong>{topic["label"]}</strong>: '
                    + ", ".join(topic["keywords"])
                    + f" <span style='color:#999'>(Docs: {topic['count']})</span></div>",
                    unsafe_allow_html=True,
                )
        elif "error" in topics:
            st.info(topics["error"])
        else:
            st.info("No topics detected")
        st.markdown("</div>", unsafe_allow_html=True)

        # Named Entity Recognition
        st.markdown('<div class="analytics-section">', unsafe_allow_html=True)
        st.markdown('<div class="analytics-title">🏷️ Named Entities (NER)</div>', unsafe_allow_html=True)
        if entities:
            entities_html = "".join(
                [
                    f'<span class="entity-tag">{e.get("word", "")} '
                    f'<span class="entity-type">[{e.get("entity_group", "")}]</span></span>'
                    for e in entities
                ]
            )
            st.markdown(entities_html, unsafe_allow_html=True)

            # Entity breakdown
            st.markdown("##### Entity Breakdown:")
            for ent in entities:
                st.markdown(
                    f"- **{ent.get('word', '')}**: {ent.get('entity_group', '')} (confidence: {ent.get('score', 0):.2f})"
                )
        else:
            st.info("No named entities detected")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        # Sentiment Analysis
        st.markdown('<div class="analytics-section">', unsafe_allow_html=True)
        st.markdown('<div class="analytics-title">😊 Sentiment Analysis</div>', unsafe_allow_html=True)

        if sentiment:
            label = sentiment.get("label", "").lower()
            score = sentiment.get("score", 0)

            sentiment_emojis = {
                "positive": "😊",
                "negative": "😞",
                "neutral": "😐",
            }
            emoji = sentiment_emojis.get(label, "🙂")
            label_cap = label.capitalize()

            # Sentiment color gradient
            sentiment_colors = {
                "positive": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "negative": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
                "neutral": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)",
            }
            gradient = sentiment_colors.get(label, "linear-gradient(135deg, #667eea 0%, #764ba2 100%)")

            st.markdown(
                f"""
            <div class="sentiment-box" style="background: {gradient};">
                <div class="sentiment-emoji">{emoji}</div>
                <h3 style="margin:0;font-size:1.5rem;">{label_cap}</h3>
                <p style="margin:10px 0 0 0;font-size:1.1rem;">Confidence: {score:.2%}</p>
            </div>
            """,
                unsafe_allow_html=True,
            )

            # Sentiment interpretation
            st.markdown("##### Interpretation:")
            if label == "positive":
                st.success("This article has a positive tone, likely discussing favorable news or outcomes.")
            elif label == "negative":
                st.error("This article has a negative tone, possibly covering concerning or unfavorable events.")
            else:
                st.info("This article maintains a neutral tone, presenting information objectively.")
        else:
            st.warning("Sentiment analysis unavailable")

        st.markdown("</div>", unsafe_allow_html=True)

        # Trend Analysis Placeholder
        st.markdown('<div class="analytics-section">', unsafe_allow_html=True)
        st.markdown('<div class="analytics-title">📈 Trend Analysis</div>', unsafe_allow_html=True)
        st.info("Trend analysis shows how this topic is performing over time. (Feature coming soon)")
        st.markdown("</div>", unsafe_allow_html=True)

    # Additional Analytics Section (Full Width)
    st.markdown('<div class="analytics-section">', unsafe_allow_html=True)
    st.markdown('<div class="analytics-title">🧠 Comprehensive Analysis Summary</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
    **Article Overview:**
    - **Total Keywords Identified:** {len(keywords)}
    - **Named Entities Found:** {len(entities)}
    - **Sentiment:** {sentiment.get('label', 'N/A').capitalize()} ({sentiment.get('score', 0):.2%} confidence)
    - **Source Credibility:** {source}
    - **Publication Date:** {published}

    **Key Insights:**
    - This article discusses **{', '.join(keywords[:3]) if keywords else 'general topics'}**
    - Primary entities mentioned include **{', '.join([e.get('word', '') for e in entities[:3]]) if entities else 'none detected'}**
    - The overall tone is **{sentiment.get('label', 'neutral').lower()}**, suggesting the article presents information in a {'factual' if sentiment.get('label', '').lower() == 'neutral' else sentiment.get('label', '').lower()} manner
    """
    )
    st.markdown("</div>", unsafe_allow_html=True)

    # Bottom back button
    st.markdown("---")
    st.button("⬅ Back to Dashboard", key="back_to_dashboard_bottom", on_click=go_back_to_dashboard)


# ----------------------------------------------------------------------------
# Cards grid helper (to avoid duplicate rendering)
# ----------------------------------------------------------------------------
def render_cards_grid(news_items, sentiment_list):
    """Render article cards in a 3-column grid, with per-card analytics button."""
    kidx = 0
    from dateutil import parser

    for i in range(0, len(news_items), 3):
        row_news = news_items[i: i + 3]
        cols = st.columns(3)
        for col, news in zip(cols, row_news):
            with col:
                # Robust image URL extraction
                image_url = get_image_url(news)
                title = news.get("title", "No Title").replace("'", "'").replace('"', "&quot;")
                source = str(news.get("source", "Unknown")).replace("'", "'")
                published = news.get("publishedAt") or news.get("published_at") or "N/A"
                if published != "N/A":
                    try:
                        dt = parser.parse(published)
                        published = dt.strftime("%b %d, %Y %H:%M")
                    except Exception:
                        pass
                description = (news.get("description") or "No description available")[:200].replace("'", "'").replace(
                    '"', "&quot;"
                )
                url = news.get("url", "#")
                sentiment = sentiment_list[kidx] if kidx < len(sentiment_list) else {}

                # Image HTML (inline within card)
                if image_url:
                    image_html = (
                        '<div style="width:100%;height:150px;overflow:hidden;border-radius:8px;'
                        'background:#c2c3c4;display:flex;align-items:center;justify-content:center;'
                        'margin-bottom:8px;">'
                        f'<img src="{image_url}" style="width:100%;height:150px;object-fit:cover;" '
                        f'onerror="this.onerror=null; this.style.display=\'none\'; this.parentElement.innerHTML=\'📰\';"/>'
                        "</div>"
                    )
                else:
                    image_html = (
                        '<div style="height:150px;display:flex;align-items:center;justify-content:center;'
                        'font-size:34px;background:#c2c3c4;border-radius:8px;margin-bottom:8px;">📰</div>'
                    )

                h3_style = "font-size:1.14rem;font-weight:600;margin-bottom:7px;margin-top:2px;color:#242423;line-height:1.3;"
                title_html = f'<h3 style="{h3_style}">{title}</h3>'

                sentiment_emojis = {"positive": "😊", "negative": "😞", "neutral": "😐"}
                sentiment_html = "<div style='margin-top:10px; margin-bottom:10px; font-size:14px; color:#242423;'>"
                if sentiment:
                    label = (sentiment.get("label") or "").lower()
                    score = float(sentiment.get("score") or 0)
                    emoji = sentiment_emojis.get(label, "🙂")
                    label_cap = label.capitalize()
                    sentiment_html += (
                        f"{emoji} <span style='font-weight:500;'>Sentiment:</span> "
                        f"<strong>{label_cap}</strong> "
                        f"<span style='font-size:12px; color:#747374;'>(confidence: {score:.2f})</span>"
                    )
                else:
                    sentiment_html += "🙂 Sentiment: N/A"
                sentiment_html += "</div>"

                kidx += 1
                card_style = (
                    "padding:16px; background:#fafbf8; border-radius:10px; "
                    "box-shadow:0 2px 12px rgba(0,0,0,0.07); margin-bottom:12px;"
                )

                st.markdown(
                    f"""
                        <div class='news-card-content' style='{card_style}'>
                            {image_html}
                            {title_html}
                            <p style='color:#747374;font-size:13px;margin:8px 0;'>🏷️ {source} &nbsp; | &nbsp; 📅 {published}</p>
                            <p style='color:#242423;font-size:14px;line-height:1.5;margin-bottom:10px;'>{description}...</p>
                            {sentiment_html}
                            <a href="{url}" target="_blank" style='color:#4a90e2;text-decoration:none;font-size:14px;font-weight:500;'>🔗 Open Article</a>
                        </div>
                    """,
                    unsafe_allow_html=True,
                )

                def go_to_analytics(article):
                    st.session_state.selected_article = article
                    st.session_state.selectedarticle = article  # mirror
                    st.session_state.page = "analytics"
                    safe_rerun()

                st.button(
                    "📊 View Analytics",
                    key=f"analytics_{kidx}",
                    use_container_width=True,
                    on_click=go_to_analytics,
                    args=(news,),
                )

    st.markdown(
        """
        <style>
        .stMarkdown h4 {margin-bottom:4px;}
        </style>
        """,
        unsafe_allow_html=True,
    )



# ----------------------------------------------------------------------------
# Dashboard
# ----------------------------------------------------------------------------
def news_dashboard():
    """Main dashboard: raw analysis, search, cached distributions, trend insights, topic modeling, and cards."""
    st.markdown('<div class="newspaper-masthead">📰 Neura News Dashboard</div>', unsafe_allow_html=True)

    with st.sidebar:
        st.markdown(f"**Logged in as:** {st.session_state.username}")
        if st.button("📰 Home / News", key="sidebar_home"):
            st.session_state.page = "news_dashboard"
            safe_rerun()
        if st.button("📊 User Dashboard", key="sidebar_dash"):
            st.session_state.page = "user_dashboard"
            safe_rerun()
        # inside with st.sidebar: in news_dashboard()
        if st.button("📈 Time Series", key="sidebar_time_series"):
            st.session_state.page = "time_series"
            safe_rerun()
        if st.button("🗺 Geo Heatmap", key="sidebar_geo"):
            st.session_state.page = "geo_map"
            safe_rerun()
        if st.button("👤 Profile", use_container_width=True):
            st.session_state.page = "profile"
            safe_rerun()
        if st.button("🔒 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.loggedin = False
            st.session_state.username = ""
            st.session_state.page = "landing"
            safe_rerun()

    # --- Raw Text Sentiment & Entity Analysis ---
    st.subheader("💬 Raw Text Sentiment & Entity Analysis")
    user_text = st.text_area("Enter any text for analysis", height=120)
    if st.button("Analyze Text"):
        if user_text.strip():
            resp = requests.post(f"{API_BASE}/analyze", data={"text": user_text})
            if resp.status_code == 200:
                result = resp.json()
                sentiment = result["sentiment"]
                st.markdown(f"**Sentiment:** `{sentiment['label']}` (confidence: {sentiment['score']:.2f})")
                entities = result["entities"]
                if entities:
                    st.markdown("**Entities:**")
                    for ent in entities:
                        st.markdown(f"- `{ent['word']}` (_{ent['entity_group']}_), confidence: {ent['score']:.2f}")
                else:
                    st.write("No entities detected.")
            else:
                st.error("Backend error")
        else:
            st.warning("Please enter text to analyze.")

    st.divider()

    # # 1) Backend guard
    # if not backend_ok():
    #     st.warning("Backend offline. Start FastAPI (uvicorn main:app --reload) and retry.")
    #     st.stop()

    # 2) Search Section
    st.markdown("### 🔎 Search News")

    col1, col2, col3 = st.columns([4, 1, 1])
    with col1:
        query = st.text_input("Search by topic / use voice", value=st.session_state.get("last_query", ""))
    with col2:
        page_size = st.selectbox("Articles per page", [5, 10, 20], index=1)
    with col3:
        lang = st.selectbox("Language", ["en", "hi", "mr", "es", "de", "zh"], index=0)

        col_vs, _ = st.columns([1, 5])
        with col_vs:
            if st.button("🎙 Voice Search"):
                recognizer = sr.Recognizer()
                try:
                    with sr.Microphone() as source:
                        st.info("Listening...")
                        audio = recognizer.listen(source, timeout=5, phrase_time_limit=8)
                    voice_text = recognizer.recognize_google(audio, language=lang)
                    st.session_state["last_query"] = voice_text.strip()
                    st.success(f"Recognized: {voice_text.strip()}")
                    safe_rerun()
                except Exception as e:
                    st.warning(f"Voice input not recognized: {e}")

    query_value = (query or st.session_state.get("last_query", "")).strip()

    # Keep locals to reuse if needed
    texts_for_keywords = []
    news_items = []
    sentiment_list = []

    if st.button("🔍 Search"):
        if not query_value:
            st.warning("Enter a search term")
        else:
            st.session_state["last_query"] = query_value
            with st.spinner("Fetching latest news..."):
                data = fetch_latest_news(query=query_value, language=lang, page_size=page_size)

            if not data or not data.get("results"):
                st.warning("No news found.")
            else:
                news_items = data["results"]

                # Persist for other sections (write both key variants)
                st.session_state["cachednews"] = news_items
                st.session_state["cached_articles"] = news_items

                # Batch NLP preparation
                texts_for_keywords = [
                    f"{(n.get('title') or '')} {str(n.get('description') or '')}".strip()
                    for n in news_items
                ]

                # Keywords
                try:
                    resp_kw = requests.post(f"{API_BASE}/extract_keywords", json=texts_for_keywords, timeout=30)
                    keywords_list = (
                        resp_kw.json().get("keywords", []) if resp_kw.status_code == 200 else [[] for _ in news_items]
                    )
                except Exception:
                    keywords_list = [[] for _ in news_items]

                # Sentiment + Entities (batch)
                try:
                    resp_an = requests.post(
                        f"{API_BASE}/analyze_batch",
                        json={"articles": texts_for_keywords},
                        timeout=60,
                    )
                    if resp_an.status_code == 200:
                        batch = resp_an.json()
                        sentiment_list = batch.get("sentiments", [{} for _ in news_items])
                        entities_list = batch.get("entities", [[] for _ in news_items])
                    else:
                        sentiment_list = [{} for _ in news_items]
                        entities_list = [[] for _ in news_items]
                except Exception:
                    sentiment_list = [{} for _ in news_items]
                    entities_list = [[] for _ in news_items]

                # Save caches (both styles for compatibility)
                st.session_state["cachedsentiments"] = sentiment_list
                st.session_state["cached_sentiments"] = sentiment_list
                st.session_state["cachedentities"] = entities_list
                st.session_state["cached_entities"] = entities_list
                st.session_state["cachedkeywords"] = keywords_list
                st.session_state["cached_keywords"] = keywords_list
                st.session_state["cachedquery"] = data.get("cleaned_query", query_value)
                st.session_state["cached_query"] = data.get("cleaned_query", query_value)
                st.session_state["cachedlang"] = lang
                st.session_state["cached_lang"] = lang

                # Optional Topic Modeling (after successful search)
                topics = []
                doc_topic_map = {}
                if len(texts_for_keywords) >= 2:
                    try:
                        with st.spinner("🔍 Identifying topics..."):
                            topic_resp = requests.post(
                                f"{API_BASE}/topics",
                                json={
                                    "articles": texts_for_keywords,
                                    "num_topics": min(5, max(1, len(texts_for_keywords) // 2)),
                                },
                                timeout=60,
                            )
                        if topic_resp.status_code == 200:
                            topic_data = topic_resp.json()
                            if "error" not in topic_data:
                                topics = topic_data.get("topics", [])
                                document_topics = topic_data.get("document_topics", [])
                                doc_topic_map = {
                                    dt.get("document_index", i): dt for i, dt in enumerate(document_topics)
                                }

                                # Display Topics
                                if topics:
                                    st.markdown("---")
                                    st.markdown("### 🎯 Discovered Topics")
                                    cols = st.columns(min(len(topics), 3))
                                    for idx, topic in enumerate(topics[:3]):
                                        with cols[idx]:
                                            st.markdown(
                                                f"""
                                                <div style='background:#4a90e220;padding:15px;border-radius:10px;text-align:center;margin-bottom:15px;'>
                                                    <h4 style='margin:0;color:#242423;font-size:1.1rem;'>Topic {topic.get('topic_id', '')}</h4>
                                                    <p style='font-size:14px;color:#565657;margin:8px 0;font-weight:500;'>{topic.get('label', '')}</p>
                                                    <p style='font-size:12px;color:#747374;margin:0;'>{topic.get('count', 0)} articles</p>
                                                </div>
                                                """,
                                                unsafe_allow_html=True,
                                            )
                            else:
                                st.info(topic_data.get("error", "Topic modeling unavailable"))
                        else:
                            st.info(f"Topic API returned {topic_resp.status_code}")
                    except Exception as e:
                        st.warning(f"Topic modeling unavailable: {e}")

                # Save topic outputs for later use (both styles)
                st.session_state["cachedtopics"] = topics
                st.session_state["cached_topics"] = topics
                st.session_state["cacheddoctopics"] = doc_topic_map
                st.session_state["cached_doc_topics"] = doc_topic_map

    # Optional quick distribution from cached results
    if st.session_state.get("cachedsentiments"):
        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
        for s in st.session_state["cachedsentiments"]:
            lbl = (s or {}).get("label", "neutral").lower()
            if lbl in sentiment_counts:
                sentiment_counts[lbl] += 1
        st.subheader("Sentiment distribution")
        st.bar_chart(pd.DataFrame.from_dict(sentiment_counts, orient="index", columns=["count"]))

    st.markdown("---")

    # 3) Trend Insights — moved to User Dashboard to avoid duplicate charts on News Dashboard
    st.info(
        "For Trend Insights (correlation, articles over time, global sentiment), open the User Dashboard from the sidebar.")
    if st.button("Open User Dashboard", key="open_user_dash_from_news"):
        st.session_state.page = "user_dashboard"
        safe_rerun()

        # # 3) Trend Insights (Analytics) — gated by login + backend health
    # if (st.session_state.get("loggedin") or st.session_state.get("logged_in")) and backend_ok():
    #     st.subheader("Trend Insights")
    #     data = fetch_trend(30)
    #     if data and data.get("points"):
    #         df = pd.DataFrame(data["points"])
    #         df["date"] = pd.to_datetime(df["date"], errors="coerce")
    #         df["topic_count"] = pd.to_numeric(df["topic_count"], errors="coerce").fillna(0).astype(int)
    #         df["avg_sentiment"] = pd.to_numeric(df["avg_sentiment"], errors="coerce").fillna(0.0)
    #
    #         topic_agg = df.groupby("topic", as_index=False).agg(
    #             topic_count=("topic_count", "sum"),
    #             avg_sentiment=("avg_sentiment", "mean"),
    #         )
    #         run_trend_insights(topic_agg)
    #
    #         st.subheader("Articles over time")
    #         by_day = df.groupby("date", as_index=False)["topic_count"].sum().set_index("date").sort_index()
    #         st.line_chart(by_day)
    #
    #         st.subheader("Sentiment distribution (global)")
    #         dist = data.get("sentiment_distribution", {})
    #         sdist = pd.Series(dist).reindex(["positive", "neutral", "negative"]).fillna(0).astype(int)
    #         st.bar_chart(sdist)
    #     else:
    #         st.info("No analytics data yet. Run a search or ingest articles first.")
    # else:
    #     st.info("Login and fetch articles to view insights.")

        # --- Topic Modeling (fallback when not using analytics endpoint) ---
        topics = []
        doc_topic_map = {}

        # Reuse local texts or rebuild from cached articles
        if texts_for_keywords:
            t_list = texts_for_keywords
            current_news = news_items or (st.session_state.get("cached_articles") or st.session_state.get("cachednews") or [])
        else:
            current_news = st.session_state.get("cached_articles") or st.session_state.get("cachednews") or []
            t_list = [
                f"{(n.get('title') or '')} {str(n.get('description') or '')}".strip() for n in current_news
            ]

        if len(t_list) >= 2:
            try:
                with st.spinner("🔍 Identifying topics..."):
                    topic_resp = requests.post(
                        f"{API_BASE}/topics",
                        json={
                            "articles": t_list,
                            "num_topics": min(5, max(1, len(t_list) // 2)),
                        },
                        timeout=60,
                    )
                if topic_resp.status_code == 200:
                    topic_data = topic_resp.json()
                    if "error" not in topic_data:
                        topics = topic_data.get("topics", [])
                        document_topics = topic_data.get("document_topics", [])
                        doc_topic_map = {dt.get("document_index", i): dt for i, dt in enumerate(document_topics)}

                        # Display Topics
                        if topics:
                            st.markdown("---")
                            st.markdown("### 🎯 Discovered Topics")
                            cols = st.columns(min(len(topics), 3))
                            for idx, topic in enumerate(topics[:3]):
                                with cols[idx]:
                                    st.markdown(
                                        f"""
                                        <div style='background:#4a90e220;padding:15px;border-radius:10px;text-align:center;margin-bottom:15px;'>
                                            <h4 style='margin:0;color:#242423;font-size:1.1rem;'>Topic {topic.get('topic_id', '')}</h4>
                                            <p style='font-size:14px;color:#565657;margin:8px 0;font-weight:500;'>{topic.get('label', '')}</p>
                                            <p style='font-size:12px;color:#747374;margin:0;'>{topic.get('count', 0)} articles</p>
                                        </div>
                                        """,
                                        unsafe_allow_html=True,
                                    )
                    else:
                        st.info(topic_data.get("error", "Topic modeling unavailable"))
                else:
                    st.info(f"Topic API returned {topic_resp.status_code}")
            except Exception as e:
                st.warning(f"Topic modeling unavailable: {e}")

        # Save topic outputs if you reference them later
        st.session_state.news_items = current_news
        st.session_state.sentiment_list = (
            st.session_state.get("cached_sentiments") or st.session_state.get("cachedsentiments") or []
        )
        st.session_state.topics = topics
        st.session_state.doc_topic_map = doc_topic_map

        # --- Topic popularity + sentiment distribution (optional quick stats) ---
        cached_topics_any = st.session_state.get("cached_topics") or st.session_state.get("cachedtopics") or []
        cached_docs_any = st.session_state.get("cached_doc_topics") or st.session_state.get("cacheddoctopics") or {}
        if cached_topics_any:
            topic_counts = {f"Topic {i}": t.get("count", 0) for i, t in enumerate(cached_topics_any)}
            for dt in cached_docs_any.values():
                topic_label = dt.get("topic_label", "Unknown")
                if topic_label in topic_counts:
                    topic_counts[topic_label] += 1
            # Optional place to visualize topic_counts if desired
            # st.bar_chart(pd.Series(topic_counts))

        sentiment_counts2 = {"positive": 0, "neutral": 0, "negative": 0}
        for s in st.session_state.get("cached_sentiments") or st.session_state.get("cachedsentiments") or []:
            lbl = (s or {}).get("label", "neutral").lower()
            if lbl in sentiment_counts2:
                sentiment_counts2[lbl] += 1
        sentiment_df = pd.DataFrame.from_dict(sentiment_counts2, orient="index", columns=["count"])
        st.markdown("### 😊 Sentiment Distribution")
        st.bar_chart(sentiment_df)

    # Cards grid (render once, reusing session caches)
    final_news = st.session_state.get("cached_articles") or st.session_state.get("cachednews") or []
    final_sent = st.session_state.get("cached_sentiments") or st.session_state.get("cachedsentiments") or []
    if final_news:
        render_cards_grid(final_news, final_sent)


def profile_page():
    """User profile page (load and update)."""
    st.markdown('<div class="newspaper-masthead">👤 Profile</div>', unsafe_allow_html=True)
    username = st.session_state.get("username", "")
    resp = requests.get(f"{API_BASE}/user/profile/{username}")
    if resp.status_code != 200:
        st.error("Unable to load profile.")
        return
    profile = resp.json()
    email = st.text_input("Email", value=profile.get("email", ""))
    language = st.selectbox("Preferred Language", ["en", "hi", "fr", "es", "de", "zh"], index=0)
    interests = st.text_input("Interests", value=profile.get("interests", ""))
    if st.button("Save Changes"):
        put = requests.put(
            f"{API_BASE}/user/profile/{username}",
            json={"email": email, "language": language, "interests": interests},
        )
        if put.status_code == 200:
            st.success("Profile updated successfully.")
        else:
            st.error("Profile update failed.")
    if st.button("⬅ Back to Dashboard"):
        st.session_state.page = "news_dashboard"
        safe_rerun()


# ----------------------------------------------------------------------------
# Visualization helpers / preserved utilities
# ----------------------------------------------------------------------------
def fetch_latest_news_with_sentiment_and_topics():
    """Direct fetch utility preserved from older code."""
    url = BACKEND_URL
    params = {"query": "", "language": "en", "page_size": 20}
    response = requests.get(url, params=params)
    if response.status_code != 200:
        st.error("Failed to fetch news data from server")
        return None
    return response.json()


# Preserve earlier excerpt semantics as a doc function (not executed)
def user_dashboard_live_excerpt():
    """
    Excerpt guidance:
    - If building df with 'sentiment_score' and 'topic1_count', map to topic_count/avg_sentiment before run_trend_insights.
    - This function is a preserved stub from the original and is not called.
    """
    pass


def user_dashboard_live():
    """User Dashboard - News Insights (robust, with Trend Insights and safe datetime handling)."""
    st.title("User Dashboard - News Insights")

    # Only show the dashboard if articles are available after user search
    if "cached_articles" not in st.session_state or not st.session_state["cached_articles"]:
        st.info("No articles available. Please search first.")
        return

    articles = st.session_state["cached_articles"]
    sentiments = st.session_state.get("cached_sentiments", [])
    topics = st.session_state.get("cached_topics", [])

    # Build lists for DataFrame and visualization
    data_rows = []
    for idx, art in enumerate(articles):
        # Capture raw date string; convert after building the DataFrame
        data_rows = []
        for idx, art in enumerate(articles):
            # Multi-key date capture (conversion later)
            pub_date = (
                    art.get("publishedAt") or
                    art.get("published_at") or
                    art.get("pubDate") or
                    art.get("published") or
                    art.get("date")
            )
            title = art.get("title")

            # Sentiment info
            sentiment_score = 0
            sentiment_label = "neutral"
            if idx < len(sentiments):
                sent = sentiments[idx] or {}
                sentiment_score = sent.get("score", 0)
                sentiment_label = (sent.get("label", "neutral") or "neutral").lower()

            # Topic info
            topic_count = len(topics[idx]) if idx < len(topics) and topics[idx] else 0

            data_rows.append(
                {
                    "title": title,
                    "sentiment_score": sentiment_score,
                    "sentiment_label": sentiment_label,
                    "topic1_count": topic_count,
                    "published_at": pub_date,
                }
            )

        title = art.get("title")
        # Sentiment info
        sentiment_score = 0
        sentiment_label = "neutral"
        if idx < len(sentiments):
            sent = sentiments[idx] or {}
            sentiment_score = sent.get("score", 0)
            sentiment_label = (sent.get("label", "neutral") or "neutral").lower()
        # Topic info (count-per-article list length if present)
        topic_count = len(topics[idx]) if idx < len(topics) and topics[idx] else 0
        data_rows.append(
            {
                "title": title,
                "sentiment_score": sentiment_score,
                "sentiment_label": sentiment_label,
                "topic1_count": topic_count,  # keep original column name for compatibility
                "published_at": pub_date,
            }
        )

    df = pd.DataFrame(data_rows)

    # Coerce dates once, upfront, and make tz-naive for plotting
    if "published_at" not in df.columns:
        df["published_at"] = pd.NaT
    df["published_at"] = pd.to_datetime(df["published_at"], errors="coerce", utc=True)
    try:
        df["published_at"] = df["published_at"].dt.tz_localize(None)
    except Exception:
        pass

    # Sentiment distribution chart
    st.subheader("Sentiment Distribution")
    if not df.empty and "sentiment_label" in df:
        sentiment_counts = df["sentiment_label"].value_counts().reindex(["positive", "neutral", "negative"], fill_value=0)
        st.bar_chart(sentiment_counts)
    else:
        st.info("No sentiments to display.")

    # Topic frequency chart
    st.subheader("Topic Frequency")
    if topics and any(topics):
        all_topics_flat = [t for sublist in topics for t in (sublist or [])]
        if all_topics_flat:
            topic_counts = pd.Series(all_topics_flat).value_counts()
            st.bar_chart(topic_counts)
        else:
            st.info("No topics found in articles.")
    else:
        st.info("No topics found in articles.")

    # Local correlation via run_trend_insights using in-session data
    # Map to expected schema: topic_count + avg_sentiment
    if not df.empty and {"sentiment_score", "topic1_count"}.issubset(df.columns):
        df2 = pd.DataFrame(
            {
                "topic_count": pd.to_numeric(df["topic1_count"], errors="coerce").fillna(0).astype(int),
                "avg_sentiment": pd.to_numeric(df["sentiment_score"], errors="coerce").fillna(0.0),
            }
        )
        run_trend_insights(df2)
    else:
        st.info("Not enough data to compute trend insights.")

    # Trend Insights (backend analytics) - render before local date chart so errors below never hide this section
    # ---------- Trend Insights (backend first, then local fallback) ----------
    st.markdown('<a name="trend-insights"></a>', unsafe_allow_html=True)
    st.subheader("Trend Insights")

    def build_local_trend_from_cache(df_local: pd.DataFrame):
        # Articles over time (local)
        st.subheader("Articles over time")
        # Coerce date from multiple keys
        if "published_at" not in df_local.columns:
            df_local["published_at"] = pd.NaT
        # If 'published_at' is string/object, we already coerced earlier; otherwise try again here
        if not pd.api.types.is_datetime64_any_dtype(df_local["published_at"]):
            df_local["published_at"] = pd.to_datetime(df_local["published_at"], errors="coerce", utc=True)
            try:
                df_local["published_at"] = df_local["published_at"].dt.tz_localize(None)
            except Exception:
                pass
        valid = df_local["published_at"].notna()
        if valid.any():
            date_series = df_local.loc[valid, "published_at"].dt.date.value_counts().sort_index()
            st.line_chart(date_series)
        else:
            st.info("No valid publication dates to plot.")

        # Global sentiment distribution (local)
        st.subheader("Sentiment distribution (global)")
        if "sentiment_label" in df_local.columns and not df_local.empty:
            counts = df_local["sentiment_label"].value_counts().reindex(["positive", "neutral", "negative"],
                                                                        fill_value=0)
            st.bar_chart(counts)
        else:
            st.info("No sentiments available in the current results.")

    # Try backend analytics
    data = fetch_trend(30)
    if data and data.get("points"):
        df_t = pd.DataFrame(data["points"])
        df_t["date"] = pd.to_datetime(df_t["date"], errors="coerce", utc=True)
        try:
            df_t["date"] = df_t["date"].dt.tz_localize(None)
        except Exception:
            pass
        df_t["topic_count"] = pd.to_numeric(df_t["topic_count"], errors="coerce").fillna(0).astype(int)
        df_t["avg_sentiment"] = pd.to_numeric(df_t["avg_sentiment"], errors="coerce").fillna(0.0)

        # Correlation (backend aggregate)
        topic_agg = df_t.groupby("topic", as_index=False).agg(
            topic_count=("topic_count", "sum"),
            avg_sentiment=("avg_sentiment", "mean"),
        )
        run_trend_insights(topic_agg)

        # Articles over time (backend)
        st.subheader("Articles over time")
        by_day = (
            df_t.dropna(subset=["date"])
            .groupby("date", as_index=False)["topic_count"].sum()
            .set_index("date").sort_index()
        )
        st.line_chart(by_day)

        # Global sentiment distribution (backend)
        st.subheader("Sentiment distribution (global)")
        dist = data.get("sentiment_distribution", {})
        sdist = pd.Series(dist).reindex(["positive", "neutral", "negative"]).fillna(0).astype(int)
        st.bar_chart(sdist)
    else:
        # Backend failed or empty -> fall back to local cached data already built earlier as df
        st.info("Using local results for insights (backend analytics unavailable).")
        # If your df didn't yet coerce dates, do it now from multiple candidate keys
        if "published_at" in df.columns and pd.api.types.is_datetime64_any_dtype(df["published_at"]):
            build_local_trend_from_cache(df)
        else:
            # Try to reconstruct 'published_at' from various common fields found in articles
            pub_candidates = []
            for art in articles:
                v = art.get("publishedAt") or art.get("published_at") or art.get("pubDate") or art.get(
                    "published") or art.get("date")
                pub_candidates.append(v)
            df["published_at"] = pd.to_datetime(pub_candidates, errors="coerce", utc=True)
            try:
                df["published_at"] = df["published_at"].dt.tz_localize(None)
            except Exception:
                pass
            build_local_trend_from_cache(df)

    # Articles Trend Over Time (local, robust)
    st.subheader("Articles Trend Over Time")
    try:
        valid = df["published_at"].notna()
        if valid.any():
            date_series = df.loc[valid, "published_at"].dt.date.value_counts().sort_index()
            st.line_chart(date_series)

            # Optional: spike/dip annotation
            mean = date_series.mean()
            std = date_series.std()
            spikes = date_series[date_series > mean + std]
            dips = date_series[date_series < mean - std]
            if not spikes.empty:
                st.markdown(f"**Spikes on:** {', '.join(str(d) for d in spikes.index)}")
            if not dips.empty:
                st.markdown(f"**Dips on:** {', '.join(str(d) for d in dips.index)}")
        else:
            st.info("No valid publication dates to plot.")
    except Exception as e:
        st.warning(f"Could not plot article dates: {e}")

    # Back button
    if st.button("🔙 Back to Home / News", key="dashboard_back_btn"):
        st.session_state.page = "news_dashboard"
        safe_rerun()



# ----------------------------------------------------------------------------
# Router
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# ----------------------------------------------------------------------------
# Routing
# ----------------------------------------------------------------------------
page = st.session_state.get("page", "landing")
is_logged_in = bool(st.session_state.get("logged_in") or st.session_state.get("loggedin"))

def _render_time_series():
    if run_time_series:
        run_time_series()
    else:
        st.error(f"Time Series page not available: {run_time_series_error or 'module not found or no run()'}")

def _render_geo():
    if run_geo_map:
        run_geo_map()
    else:
        st.error(f"Geo page not available: {run_geo_map_error or 'module not found'}")

if page == "admin_login":
    admin_login_page()
elif page == "admin_dashboard":
    admin_dashboard_page()
else:
    if not is_logged_in:
        # Unauthenticated
        if page == "landing":
            landing_page()
        elif page == "register":
            register_page()
        elif page == "time_series":
            _render_time_series()
        elif page == "geo_map":
            _render_geo()
        else:
            # default for unauthenticated
            login_page()
    else:
        # Authenticated
        if page == "profile":
            profile_page()
        elif page == "analytics":
            article_analytics_page()
        elif page == "user_dashboard":
            user_dashboard_live()
        elif page == "time_series":
            _render_time_series()
        elif page == "geo_map":
            _render_geo()
        else:
            # default for authenticated
            news_dashboard()
