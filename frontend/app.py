import streamlit as st
import requests
import sys
import os
import re
import speech_recognition as sr
from streamlit_mic_recorder import speech_to_text



# ----------------------------------------------------------------------------
# Temporarily
# ----------------------------------------------------------------------------


def safe_rerun():
    # Prefer official API if present
    if hasattr(st, "experimental_rerun"):
        try:
            st.experimental_rerun()
            return
        except Exception:
            pass
    # Some installations expose st.rerun() (undocumented)
    if hasattr(st, "rerun"):
        try:
            st.rerun()
            return
        except Exception:
            pass
    # Last-resort: nudge session_state to force a redraw next run
    st.session_state["_force_refresh"] = st.session_state.get("_force_refresh", 0) + 1





# ----------------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------------
st.set_page_config(
    page_title="Neura News",
    page_icon="📰",
    layout="wide",
    initial_sidebar_state="expanded"
)

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.auth_service import register_user, login_user

BACKEND_URL = "http://127.0.0.1:8000/news"

# ----------------------------------------------------------------------------
# CSS - Unified Modern Design
# ----------------------------------------------------------------------------
st.markdown("""
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
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------------------------
# Utility
# ----------------------------------------------------------------------------
def is_valid_email(email: str) -> bool:
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

# ----------------------------------------------------------------------------
# Landing Page
# ----------------------------------------------------------------------------
def landing_page():
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
        st.markdown('<div class="feature-card">💬 Analyze sentiment & entities in any text</div>',
                    unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="feature-card">🎙️ Voice-enabled search and interaction</div>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        if st.button("👤 Login", key="landing_login"):
            st.session_state.page = "login"
            safe_rerun()

    with col2:
        if st.button("📝 Register", key="landing_register"):
            st.session_state.page = "register"
            safe_rerun()

    st.markdown("---")

    st.subheader("How Neura News Works")
    st.write("""
    - **Real-time News Aggregation:** Collects articles from trusted global sources to keep you updated.
    - **AI-Powered Insights:** Identifies sentiment and key entities in news to give deeper context.
    - **Customizable Searches:** Filter news by language, topic, and volume to get exactly what interests you.
    - **Voice Search:** Conveniently search news hands-free using voice input.
    - **User Profiles:** Save preferences, receive personalized recommendations, and manage your interests.
    """)

    st.markdown("---")

    st.subheader("Why Neura News?")
    st.write("""
    - **Accurate & Up-to-Date:** Powered by advanced AI and fast backend APIs.
    - **User Friendly:** Clean, modern, and intuitive interface designed for all users.
    - **Secure:** Robust authentication keeps your account and preferences private.
    - **Transparent:** Ethical news sourcing and analysis to keep you well-informed.
    """)

    st.markdown("---")

    st.subheader("About")
    st.write("""
    Neura News is built with Streamlit and backed by powerful AI services.
    It provides detailed sentiment insights, keyword extraction, and a seamless news reading experience.
    \nExplore the latest trends and stories with confidence and ease.
    """)

    st.markdown("---")

    st.subheader("Get Started")
    st.write("""
    Join thousands of users staying ahead with Neura News. Whether you want quick updates or in-depth analysis,
    this platform simplifies your news experience with AI-enhanced features.
    """)


# ----------------------------------------------------------------------------
# Authentication Pages
# ----------------------------------------------------------------------------
def login_page():
    st.markdown('<div class="newspaper-masthead">🔐 Login</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        identifier = st.text_input("Username or Email")
        password = st.text_input("Password", type="password")
        if st.button("🔓 Login", use_container_width=True):
            success, user = login_user(identifier, password)
            if success:
                st.session_state.logged_in = True
                st.session_state.username = user.username
                st.session_state.page = "dashboard"
                st.success(f"Welcome, {user.username}!")
                safe_rerun()
            else:
                st.error("Incorrect username/email or password")

        if st.button("📝 Go to Registration", use_container_width=True):
            st.session_state.page = "register"
            safe_rerun()


def register_page():
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

# ----------------------------------------------------------------------------
# Dashboard and News
# ----------------------------------------------------------------------------
def news_dashboard():
    st.markdown('<div class="newspaper-masthead">📰 Neura News Dashboard</div>', unsafe_allow_html=True)
    with st.sidebar:
        st.markdown(f"**Logged in as:** {st.session_state.username}")
        if st.button("👤 Profile", use_container_width=True):
            st.session_state.page = "profile"
            safe_rerun()
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.username = ""
            st.session_state.page = "landing"
            safe_rerun()

    # --- Raw Text Sentiment & Entity Analysis ---
    st.subheader("💬 Raw Text Sentiment & Entity Analysis")
    user_text = st.text_area("Enter any text for analysis", height=120)
    if st.button("Analyze Text"):
        if user_text.strip():
            resp = requests.post("http://127.0.0.1:8000/analyze", data={"text": user_text})
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

    # --- News Search Section ---
    st.subheader("🔎 Search News")
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        query = st.text_input("Search by topic / use voice")
    with col2:
        page_size = st.selectbox("Articles per page", [5, 10, 15, 20])
    with col3:
        lang = st.selectbox("Language", ["en", "hi", "fr", "es", "de", "zh"])

    if st.button("🎤 Voice Search"):
        recognizer = sr.Recognizer()
        with sr.Microphone() as source:
            st.info("Listening...")
            audio = recognizer.listen(source)
            try:
                query_voice = recognizer.recognize_google(audio, language=lang)
                st.session_state.last_query = query_voice
                st.success(f"Recognized: {query_voice}")
            except Exception:
                st.warning("Voice input not recognized.")

    if st.button("🔍 Search") or st.session_state.get("last_query"):
        query_value = query or st.session_state.get("last_query", "")
        if not query_value.strip():
            st.warning("Enter a search term")
        else:
            with st.spinner("Fetching latest news..."):
                resp = requests.get(BACKEND_URL, params={"query": query_value, "page_size": page_size, "language": lang})
                if resp.status_code == 200:
                    data = resp.json()
                    news_items = data.get("results", [])
                    cleaned_query = data.get("cleaned_query", query_value)
                    if not news_items:
                        st.warning("No news found.")
                    else:
                        # Only here, and only once
                        st.markdown(f"""
                            <div style='background: white; padding: 15px; border-radius: 8px; margin: 20px 0;'>
                                <p style='margin: 0; color: #242423;'>Showing <strong>{len(news_items)}</strong> articles for '<strong>{cleaned_query}</strong>' in <strong>{lang.upper()}</strong></p>
                            </div>
                        """, unsafe_allow_html=True)

                        # --- Batch keyword + sentiment/entity extraction ---
                        texts_for_keywords = [
                            (news.get("title","")+ " "+ str(news.get("description","")))
                            for news in news_items
                        ]

                        try:
                            resp = requests.post("http://127.0.0.1:8000/extract_keywords", json=texts_for_keywords)
                            keywords_list = resp.json().get("keywords", []) if resp.status_code==200 else [[] for _ in news_items]
                        except:
                            keywords_list = [[] for _ in news_items]

                        try:
                            analysis_resp = requests.post("http://127.0.0.1:8000/analyze_batch", json=texts_for_keywords)
                            if analysis_resp.status_code == 200:
                                batch = analysis_resp.json()
                                sentiment_list = batch.get("sentiments", [{} for _ in news_items])
                                entities_list = batch.get("entities", [[] for _ in news_items])
                            else:
                                sentiment_list = [{} for _ in news_items]
                                entities_list = [[] for _ in news_items]
                        except:
                            sentiment_list = [{} for _ in news_items]
                            entities_list = [[] for _ in news_items]

                        kidx = 0
                        from dateutil import parser
                        for i in range(0, len(news_items), 3):
                            row_news = news_items[i:i+3]
                            cols = st.columns(3)
                            for col, news in zip(cols, row_news):
                                with col:
                                    image_url = news.get("image") or news.get("image_url") or news.get("urlToImage") or ""
                                    title = news.get('title','No Title').replace("'", "&#39;").replace('"', '&quot;')
                                    source = news.get('source','Unknown').replace("'","&#39;")
                                    published = news.get('publishedAt','N/A')
                                    if published != 'N/A':
                                        try:
                                            dt = parser.parse(published)
                                            published = dt.strftime('%b %d, %Y %H:%M')
                                        except:
                                            pass
                                    description = news.get('description','No description available')[:200].replace("'", "&#39;").replace('"', '&quot;')
                                    url = news.get('url','#')
                                    keywords = keywords_list[kidx] if kidx < len(keywords_list) else []
                                    sentiment = sentiment_list[kidx] if kidx < len(sentiment_list) else {}
                                    entities = entities_list[kidx] if kidx < len(entities_list) else []

                                    # --- ENTITY DISPLAY ---
                                    if entities:
                                        entities_html = (
                                            "<div style='margin-top:6px; margin-bottom:2px;'>"
                                            + " ".join(
                                                f"<span style='background:#c2c3c470;color:#747374;padding:2px 6px; border-radius:5px; margin-right:3px; font-size:12px;'>{e.get('word','')} <span style='color:#565657;font-size:11px;'>[{e.get('entity_group','')}]</span></span>"
                                                for e in entities)
                                            + "</div>")
                                    else:
                                        entities_html = "<div style='margin-top:6px; font-size:12px; color:#97989a;'>No entities</div>"

                                    # --- IMAGE ---
                                    if image_url:
                                        image_html = (
                                            '<div style="width:100%;height:150px;overflow:hidden;border-radius:8px;'
                                            'background:#c2c3c4;display:flex;align-items:center;justify-content:center;'
                                            'margin-bottom:8px;">'
                                            f'<img src="{image_url}" style="width:auto;max-width:100%;max-height:140px;object-fit:contain;"/>'
                                            '</div>')
                                    else:
                                        image_html = '<div style="height:150px;display:flex;align-items:center;justify-content:center;font-size:34px;background:#c2c3c4;border-radius:8px;margin-bottom:8px;">📰</div>'

                                    h3_style = "font-size:1.14rem;font-weight:600;margin-bottom:7px;margin-top:2px;color:#242423;line-height:1.3;"
                                    title_html = f'<h3 style="{h3_style}">{title}</h3>'

                                    # --- KEYWORDS ---
                                    if keywords:
                                        keywords_html = (
                                            "<div style='margin-top:6px; margin-bottom:2px;'>"
                                            + " ".join(
                                                f"<span style='background:#c2c3c420;color:#565657;padding:2px 6px; border-radius:5px; margin-right:3px; font-size:12px;'>{k}</span>" for k in keywords)
                                            + "</div>")
                                    else:
                                        keywords_html = "<div style='margin-top:6px; font-size:12px; color:#97989a;'>No keywords</div>"

                                    # --- SENTIMENT ---
                                    sentiment_emojis = {
                                        "positive": "😊",
                                        "negative": "😞",
                                        "neutral": "😐"
                                    }
                                    sentiment_html = "<div style='margin-top:10px; margin-bottom:4px; font-size:14px; color:#242423;'>"
                                    if sentiment:
                                        label = sentiment.get('label','').lower()
                                        score = sentiment.get('score',0)
                                        emoji = sentiment_emojis.get(label,"🙂")
                                        label_cap = label.capitalize()
                                        sentiment_html += f"{emoji} <span style='font-weight:500;'>Sentiment:</span> <strong>{label_cap}</strong> <span style='font-size:12px; color:#747374;'>(confidence: {score:.2f})</span>"
                                    else:
                                        emoji = "🙂"
                                        sentiment_html += f"{emoji} Sentiment: N/A"
                                    sentiment_html += "</div>"

                                    kidx += 1
                                    card_style = (
                                        "padding:16px; background:#fafbf8; border-radius:10px; "
                                        "box-shadow:0 2px 12px rgba(0,0,0,0.07); margin-bottom:12px;"
                                    )
                                    st.markdown(f"""
                                        <div class='news-card-content' style='{card_style}'>
                                            {image_html}
                                            {title_html}
                                            <p class='source-info'>🏷️ {source} &nbsp; | &nbsp; 📅 {published}</p>
                                            <p class='news-desc'>{description}...</p>
                                            {keywords_html}
                                            {entities_html}
                                            {sentiment_html}
                                            <a href="{url}" target="_blank" class="news-link">🔗 Open Article</a>
                                        </div>""", unsafe_allow_html=True)
                else:
                    st.error(f"Backend error: {resp.status_code}")

    st.markdown("""
    <style>
    .stMarkdown h4 {margin-bottom:4px;}
    </style>
    """, unsafe_allow_html=True)


# ----------------------------------------------------------------------------
# Profile Page
# ----------------------------------------------------------------------------
def profile_page():
    st.markdown('<div class="newspaper-masthead">👤 Profile</div>', unsafe_allow_html=True)
    username = st.session_state.get("username", "")
    resp = requests.get(f"http://127.0.0.1:8000/user/profile/{username}")
    if resp.status_code != 200:
        st.error("Unable to load profile.")
        return
    profile = resp.json()
    email = st.text_input("Email", value=profile["email"])
    language = st.selectbox("Preferred Language", ["en", "hi", "fr", "es", "de", "zh"], index=0)
    interests = st.text_input("Interests", value=profile["interests"])
    if st.button("Save Changes"):
        put = requests.put(f"http://127.0.0.1:8000/user/profile/{username}", json={
            "email": email, "language": language, "interests": interests
        })
        if put.status_code == 200:
            st.success("Profile updated successfully.")
        else:
            st.error("Profile update failed.")
    if st.button("⬅ Back to Dashboard"):
        st.session_state.page = "dashboard"
        safe_rerun()


# ----------------------------------------------------------------------------
# Main App Routing
# ----------------------------------------------------------------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "landing"

page = st.session_state.page

if not st.session_state.logged_in:
    if page == "landing":
        landing_page()
    elif page == "register":
        register_page()
    else:
        login_page()
else:
    if page == "profile":
        profile_page()
    else:
        news_dashboard()
