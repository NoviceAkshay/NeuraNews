import streamlit as st
import requests
import sys
import os
import re
import speech_recognition as sr
import pandas as pd
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

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "page" not in st.session_state:
    st.session_state.page = "landing"
if "selected_article" not in st.session_state:
    st.session_state.selected_article = None

# Cache for search results and analytics
if "cached_news" not in st.session_state:
    st.session_state.cached_news = []
if "cached_keywords" not in st.session_state:
    st.session_state.cached_keywords = []
if "cached_sentiments" not in st.session_state:
    st.session_state.cached_sentiments = []
if "cached_entities" not in st.session_state:
    st.session_state.cached_entities = []
if "cached_query" not in st.session_state:
    st.session_state.cached_query = ""
if "cached_lang" not in st.session_state:
    st.session_state.cached_lang = "en"

if "cached_topics" not in st.session_state:
    st.session_state.cached_topics = []
if "cached_doc_topics" not in st.session_state:
    st.session_state.cached_doc_topics = {}


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
# Article Analytics Detail Page
# ----------------------------------------------------------------------------
def article_analytics_page():
    st.markdown('<div class="newspaper-masthead">📊 Article Analytics</div>', unsafe_allow_html=True)

    # Back button at the top
    def go_back_to_dashboard():
        st.session_state.page = "dashboard"
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
            unsafe_allow_html=True)

    # Title
    title = article.get('title', 'No Title')
    st.markdown(f'<h1 class="article-title-large">{title}</h1>', unsafe_allow_html=True)

    # Meta information
    source = article.get('source', 'Unknown')
    published = article.get('publishedAt', 'N/A')
    if published != 'N/A':
        try:
            from dateutil import parser
            dt = parser.parse(published)
            published = dt.strftime('%B %d, %Y at %H:%M')
        except:
            pass

    st.markdown(f'<p class="article-meta">🏷️ <strong>{source}</strong> &nbsp;|&nbsp; 📅 {published}</p>',
                unsafe_allow_html=True)

    # Description/Full text
    description = article.get('description', 'No description available')
    st.markdown(f'<p class="article-description-full">{description}</p>', unsafe_allow_html=True)

    # Open article button
    url = article.get('url', '#')
    st.markdown(f'<a href="{url}" target="_blank" class="open-article-btn">🔗 Open Full Article</a>',
                unsafe_allow_html=True)

    st.markdown('</div>', unsafe_allow_html=True)

    # Analytics Section
    st.markdown("---")
    st.markdown('<h2 style="text-align:center;color:#242423;margin:30px 0;">📈 Detailed Analytics</h2>',
                unsafe_allow_html=True)

    # Prepare text for analysis
    analysis_text = (article.get("title", "") + " " + str(article.get("description", "")))

    with st.spinner("🔄 Analyzing article..."):
        # Fetch all analytics
        keywords = []
        sentiment = {}
        entities = []

        # Keywords Extraction
        try:
            resp = requests.post("http://127.0.0.1:8000/extract_keywords", json=[analysis_text])
            if resp.status_code == 200:
                keywords = resp.json().get("keywords", [[]])[0]
        except Exception as e:
            st.warning(f"Keywords extraction failed: {e}")

        # Sentiment & Entity Analysis
        try:
            resp = requests.post("http://127.0.0.1:8000/analyze", data={"text": analysis_text})
            if resp.status_code == 200:
                result = resp.json()
                sentiment = result.get("sentiment", {})
                entities = result.get("entities", [])
        except Exception as e:
            st.warning(f"Sentiment/Entity analysis failed: {e}")

    # Display analytics in organized sections
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
        st.markdown('</div>', unsafe_allow_html=True)

        # Named Entity Recognition
        st.markdown('<div class="analytics-section">', unsafe_allow_html=True)
        st.markdown('<div class="analytics-title">🏷️ Named Entities (NER)</div>', unsafe_allow_html=True)
        if entities:
            entities_html = "".join([
                f'<span class="entity-tag">{e.get("word", "")} <span class="entity-type">[{e.get("entity_group", "")}]</span></span>'
                for e in entities
            ])
            st.markdown(entities_html, unsafe_allow_html=True)

            # Entity breakdown
            st.markdown("##### Entity Breakdown:")
            for ent in entities:
                st.markdown(
                    f"- **{ent.get('word', '')}**: {ent.get('entity_group', '')} (confidence: {ent.get('score', 0):.2f})")
        else:
            st.info("No named entities detected")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        # Sentiment Analysis
        st.markdown('<div class="analytics-section">', unsafe_allow_html=True)
        st.markdown('<div class="analytics-title">😊 Sentiment Analysis</div>', unsafe_allow_html=True)

        if sentiment:
            label = sentiment.get('label', '').lower()
            score = sentiment.get('score', 0)

            sentiment_emojis = {
                "positive": "😊",
                "negative": "😞",
                "neutral": "😐"
            }
            emoji = sentiment_emojis.get(label, "🙂")
            label_cap = label.capitalize()

            # Sentiment color gradient
            sentiment_colors = {
                "positive": "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
                "negative": "linear-gradient(135deg, #f093fb 0%, #f5576c 100%)",
                "neutral": "linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)"
            }
            gradient = sentiment_colors.get(label, "linear-gradient(135deg, #667eea 0%, #764ba2 100%)")

            st.markdown(f"""
            <div class="sentiment-box" style="background: {gradient};">
                <div class="sentiment-emoji">{emoji}</div>
                <h3 style="margin:0;font-size:1.5rem;">{label_cap}</h3>
                <p style="margin:10px 0 0 0;font-size:1.1rem;">Confidence: {score:.2%}</p>
            </div>
            """, unsafe_allow_html=True)

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

        st.markdown('</div>', unsafe_allow_html=True)

        # Trend Analysis Placeholder
        st.markdown('<div class="analytics-section">', unsafe_allow_html=True)
        st.markdown('<div class="analytics-title">📈 Trend Analysis</div>', unsafe_allow_html=True)
        st.info("Trend analysis shows how this topic is performing over time. (Feature coming soon)")
        st.markdown('</div>', unsafe_allow_html=True)

    # Additional Analytics Section (Full Width)
    st.markdown('<div class="analytics-section">', unsafe_allow_html=True)
    st.markdown('<div class="analytics-title">🧠 Comprehensive Analysis Summary</div>', unsafe_allow_html=True)

    st.markdown(f"""
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
    """)

    st.markdown('</div>', unsafe_allow_html=True)

    # Bottom back button
    st.markdown("---")
    st.button("⬅ Back to Dashboard", key="back_to_dashboard_bottom", on_click=go_back_to_dashboard)


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
        query_value = query or st.session_state.get("last_query", "") # prioritizes manual text input (query) but falls back to the voice query (last_query)
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

                        # ✨ NEW: Topic Modeling
                        topics = []
                        doc_topic_map = {}

                        if len(texts_for_keywords) >= 2:
                            try:
                                with st.spinner("🔍 Identifying topics..."):
                                    topic_resp = requests.post("http://127.0.0.1:8000/topics", json={
                                        "articles": texts_for_keywords,
                                        "num_topics": min(5, len(texts_for_keywords) // 2)
                                    })

                                    if topic_resp.status_code == 200:
                                        topic_data = topic_resp.json()

                                        if "error" not in topic_data:
                                            topics = topic_data.get("topics", [])
                                            document_topics = topic_data.get("document_topics", [])
                                            doc_topic_map = {dt['document_index']: dt for dt in document_topics}

                                            # ✨ Display Topics Section
                                            if topics:
                                                st.markdown("---")
                                                st.markdown("### 🎯 Discovered Topics")

                                                cols = st.columns(min(len(topics), 3))
                                                for idx, topic in enumerate(topics[:3]):
                                                    with cols[idx]:
                                                        st.markdown(f"""
                                                        <div style='background:#4a90e220;padding:15px;border-radius:10px;text-align:center;margin-bottom:15px;'>
                                                            <h4 style='margin:0;color:#242423;font-size:1.1rem;'>Topic {topic['topic_id']}</h4>
                                                            <p style='font-size:14px;color:#565657;margin:8px 0;font-weight:500;'>{topic['label']}</p>
                                                            <p style='font-size:12px;color:#747374;margin:0;'>{topic['count']} articles</p>
                                                        </div>
                                                        """, unsafe_allow_html=True)
                                        else:
                                            st.info(topic_data.get("error", "Topic modeling unavailable"))
                            except Exception as e:
                                st.warning(f"Topic modeling unavailable: {e}")


                        # Prepare data for topic popularity and sentiment distribution
                        if st.session_state.cached_topics:
                            # Count articles per topic label
                            topic_counts = {topic['label']: 0 for topic in st.session_state.cached_topics}
                            for dt in st.session_state.cached_doc_topics.values():
                                topic_label = dt.get("topic_label", "Unknown")
                                if topic_label in topic_counts:
                                    topic_counts[topic_label] += 1

                            # Display topic popularity bar chart
                            st.markdown("### 📊 Articles per Topic")
                            st.bar_chart(pd.Series(topic_counts))

                        # Sentiment Distribution
                        # st.write("DEBUG sentiment_counts:", sentiment_counts)
                        st.write("DEBUG cached_sentiments sample:", st.session_state.cached_sentiments[:3])

                        sentiment_counts = {"positive": 0, "neutral": 0, "negative": 0}
                        for sentiment in st.session_state.cached_sentiments:
                            lbl = sentiment.get("label", "neutral").lower()
                            if lbl in sentiment_counts:
                                sentiment_counts[lbl] += 1
                        st.write("DEBUG sentiment_counts:", sentiment_counts)

                        sentiment_df = pd.DataFrame.from_dict(sentiment_counts, orient="index", columns=["count"])
                        st.markdown("### 😊 Sentiment Distribution")
                        st.bar_chart(sentiment_df)

                        kidx = 0
                        from dateutil import parser
                        for i in range(0, len(news_items), 3):
                            row_news = news_items[i:i + 3]
                            cols = st.columns(3)
                            for col, news in zip(cols, row_news):
                                with col:
                                    image_url = news.get("image") or news.get("image_url") or news.get(
                                        "urlToImage") or ""
                                    title = news.get('title', 'No Title').replace("'", "'").replace('"', '&quot;')
                                    source = news.get('source', 'Unknown').replace("'", "'")
                                    published = news.get('publishedAt', 'N/A')
                                    if published != 'N/A':
                                        try:
                                            dt = parser.parse(published)
                                            published = dt.strftime('%b %d, %Y %H:%M')
                                        except:
                                            pass
                                    description = news.get('description', 'No description available')[:200].replace("'",
                                                                                                                    "'").replace(
                                        '"', '&quot;')
                                    url = news.get('url', '#')
                                    sentiment = sentiment_list[kidx] if kidx < len(sentiment_list) else {}

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

                                    # --- SENTIMENT (ONLY) ---
                                    sentiment_emojis = {
                                        "positive": "😊",
                                        "negative": "😞",
                                        "neutral": "😐"
                                    }
                                    sentiment_html = "<div style='margin-top:10px; margin-bottom:10px; font-size:14px; color:#242423;'>"
                                    if sentiment:
                                        label = sentiment.get('label', '').lower()
                                        score = sentiment.get('score', 0)
                                        emoji = sentiment_emojis.get(label, "🙂")
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

                                    # CLEAN CARD - Only essentials, NO keywords/entities
                                    st.markdown(f"""
                                        <div class='news-card-content' style='{card_style}'>
                                            {image_html}
                                            {title_html}
                                            <p style='color:#747374;font-size:13px;margin:8px 0;'>🏷️ {source} &nbsp; | &nbsp; 📅 {published}</p>
                                            <p style='color:#242423;font-size:14px;line-height:1.5;margin-bottom:10px;'>{description}...</p>
                                            {sentiment_html}
                                            <a href="{url}" target="_blank" style='color:#4a90e2;text-decoration:none;font-size:14px;font-weight:500;'>🔗 Open Article</a>
                                        </div>""", unsafe_allow_html=True)

                                    # View Analytics Button
                                    def go_to_analytics(article):
                                        st.session_state.selected_article = article
                                        st.session_state.page = "analytics"

                                    st.button("📊 View Analytics", key=f"analytics_{kidx}", use_container_width=True,on_click=go_to_analytics, args=(news,))

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
    elif page == "analytics":
        article_analytics_page()
    else:
        news_dashboard()
