import streamlit as st
import requests
import sys
import os
import re
from streamlit_mic_recorder import speech_to_text
import speech_recognition as sr




st.set_page_config(
    page_title="Neura News",
    page_icon="E:\Dev\PyCharm\AppNews\assets\neura-logo.png",
    layout="wide"
)

# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from backend.auth_service import register_user, login_user

BACKEND_URL = "http://127.0.0.1:8000/news"

COLORS = {
    "light_gray": "#c2c3c4",
    "dark_bg": "#242423",
    "medium_gray": "#565657",
    "off_white": "#fafbf8",
    "light_medium_gray": "#97989a",
    "medium_dark_gray": "#747374",
    "dark_gray": "#414141",
    "light_beige": "#e5e4e3"
}

def load_css():
    st.markdown(f"""
        <style>
        body {{ background-color: {COLORS['dark_bg']}; }}
        .main {{ background-color: {COLORS['off_white']}; }}
        [data-testid="stSidebar"] {{ background-color: {COLORS['light_beige']}; }}
        .stButton>button {{ background-color: {COLORS['medium_gray']}; color: {COLORS['off_white']}; border-radius: 8px; padding: 8px 20px; font-weight: 500; }}
        .stButton>button:hover {{ background-color: {COLORS['dark_gray']}; }}
        .dashboard-header {{ background: linear-gradient(135deg, {COLORS['medium_gray']} 0%, {COLORS['dark_gray']} 100%); color: {COLORS['off_white']}; padding: 30px; border-radius: 12px; margin-bottom: 30px; text-align: center; }}
        .filter-section {{ background: {COLORS['light_beige']}; padding: 2px; border-radius: 12px; margin-bottom: 20px; }}
        .news-card-content {{ background: {COLORS['off_white']}; border-radius: 12px; padding: 16px; margin-bottom: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); height: 520px; display: flex; flex-direction: column; }}
        .news-card-content:hover {{ transform: translateY(-5px); box-shadow: 0 8px 18px rgba(0,0,0,0.2); }}
        .news-image-container {{ width: 100%; height: 220px; overflow: hidden; border-radius: 8px; background: {COLORS['light_gray']}; display: flex; align-items: center; justify-content: center; }}
        .news-image-container img, .news-image {{ width: 100%; height: 100%; object-fit: cover; border-radius: 8px; }}
        .news-image-container.placeholder {{ background: linear-gradient(135deg, {COLORS['medium_gray']}, {COLORS['dark_gray']}); color: {COLORS['off_white']}; font-size: 40px; }}
        .news-title {{ font-size: 18px; font-weight: 600; color: {COLORS['dark_bg']}; margin-top: 5px; margin-bottom: 6px; }}
        .source-info {{ color: {COLORS['medium_dark_gray']}; font-size: 14px; margin-bottom: 8px; }}
        .news-desc {{ color: {COLORS['dark_gray']}; line-height: 1.6; font-size: 15px; }}
        .news-link {{ color: {COLORS['medium_gray']}; font-weight: 500; }}
        </style>
    """, unsafe_allow_html=True)

def is_valid_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

def login():
    st.title("🔐 Login")
    with st.form("login_form"):
        identifier = st.text_input("Username or Email", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        submitted = st.form_submit_button("Login")
        if submitted:
            success, user = login_user(identifier, password)
            if success:
                st.session_state["logged_in"] = True
                st.session_state["username"] = user.username
                st.success(f"Welcome, {user.username}!")
                st.session_state["current_page"] = "Dashboard"
            else:
                st.error("Incorrect username/email or password")

    if st.button("Go to Registration"):
        st.session_state["show_login"] = False

def register():
    st.title("📝 Register")
    with st.form("register_form"):
        username = st.text_input("Choose a username", key="reg_user")
        email = st.text_input("Email Address", key="reg_email")
        password = st.text_input("Choose a password", type="password", key="reg_pass")
        confirm = st.text_input("Confirm password", type="password", key="reg_confirm")
        submitted = st.form_submit_button("Register")
        if submitted:
            if not username or not password or not confirm or not email:
                st.warning("All fields are required")
            elif password != confirm:
                st.warning("Passwords do not match")
            elif not is_valid_email(email):
                st.warning("Please enter a valid email address")
            else:
                success, message = register_user(username, email, password)
                if success:
                    st.success(message)
                    st.session_state["show_login"] = True
                else:
                    st.error(message)

def profile_management():
    st.title("👤 User Profile")
    username = st.session_state.get("username", "")
    resp = requests.get(f"http://127.0.0.1:8000/user/profile/{username}")
    if resp.status_code != 200:
        st.error("Unable to fetch profile details.")
        return
    profile = resp.json()
    language_options = ["en", "hi", "fr", "es", "de", "zh"]
    with st.form("profile_form"):
        st.markdown(f"**Username:** {profile['username']}")
        email = st.text_input("Email", value=profile["email"])
        language = st.selectbox(
            "Preferred Language",
            language_options,
            index=language_options.index(profile["language"]) if profile["language"] in language_options else 0
        )
        interests = st.text_input("Interests (comma separated)", value=profile["interests"])
        submitted = st.form_submit_button("Update Profile")
        if submitted:
            payload = {"email": email, "language": language, "interests": interests}
            put_resp = requests.put(
                f"http://127.0.0.1:8000/user/profile/{username}",
                json=payload
            )
            if put_resp.status_code == 200:
                st.session_state["lang"] = language
                st.success("Profile updated successfully!")
            else:
                st.error(f"Failed to update profile: {put_resp.text}")
    if st.button("⬅️ Back to Dashboard"):
        st.session_state["current_page"] = "Dashboard"
        st.rerun()

def sidebar_navigation():
    with st.sidebar:
        st.markdown(f"""
            <div style='text-align: center; padding: 20px 0; border-bottom: 2px solid {COLORS['medium_gray']};'>
                <img src="assets/neura-logo.png" style='width:120px; height:auto; margin-bottom:10px;'/>
                <h2 style='color: {COLORS['dark_bg']}; margin:0;'>Neura News</h2>
                <p style='color: {COLORS['medium_dark_gray']}; font-size: 12px; margin:5px 0 0 0;'>Stay Informed</p>
            </div>""", unsafe_allow_html=True)
        if st.button("📊 Dashboard"):
            st.session_state["current_page"] = "Dashboard"
            st.experimental_rerun()
        if st.button("👤 Profile"):
            st.session_state["current_page"] = "Profile"
            st.experimental_rerun()
        st.markdown(f"""
            <div style='background: {COLORS['light_gray']}; padding:10px; border-radius:8px; margin-bottom:10px; text-align:center;'>
                <p style='color: {COLORS['dark_bg']}; margin:0; font-size:14px;'>👤 {st.session_state['username']}</p>
            </div>""", unsafe_allow_html=True)

        st.markdown("""
            <div style='...'>
                <img src="assets/neura-logo.png" style='width:120px; height:auto; margin-bottom:10px;'/>
                ...
            </div>
        """, unsafe_allow_html=True)


        if st.button("🚪 Logout"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.experimental_rerun()

def news_dashboard():
    load_css()
    sidebar_navigation()
    st.markdown(f"""
        <div class='dashboard-header'>
            <h1>Neura News Dashboard</h1>
            <p>Discover the latest news and insights</p>
        </div>""", unsafe_allow_html=True)
    st.markdown("<div class='filter-section'>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([3, 1, 1])
    with col3:
        language = st.selectbox("Language", ["en", "hi", "fr", "es", "de", "zh"], index=0)
    with col1:
        if st.button("🎤 Start Voice Search"):
            recognizer = sr.Recognizer()
            with sr.Microphone() as source:
                st.info("Listening for your search...")
                audio = recognizer.listen(source)
                try:
                    query = recognizer.recognize_google(audio, language=language)
                    st.session_state["last_voice_query"] = query
                    st.success(f"Recognized: {query}")
                except sr.UnknownValueError:
                    st.warning("Didn't get any speech, please try again.")
                    st.session_state["last_voice_query"] = ""
        query = st.text_input("🔍 Search for news", value=st.session_state.get("last_voice_query", ""), placeholder="Enter a topic or speak")
    with col2:
        page_size = st.selectbox("Articles", [5, 10, 15, 20], index=0)
    search_button = st.button("🔎 Search News", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)
    if search_button or (st.session_state.get("last_voice_query", "").strip() != "" and not search_button):
        if not query.strip():
            st.warning("⚠️ Please enter a search term")
        else:
            with st.spinner("🔄 Fetching latest news..."):
                try:
                    response = requests.get(BACKEND_URL, params={"query": query, "page_size": page_size, "language": language})
                    if response.status_code == 200:
                        data = response.json()
                        news_items = data.get("results", [])
                        cleaned_query = data.get("cleaned_query", query)
                        st.markdown(f"""
                            <div style='background: white; padding: 15px; border-radius: 8px; margin: 20px 0;'>
                                <p style='margin: 0; color: {COLORS['dark_bg']};'>Showing <strong>{len(news_items)}</strong> articles for '<strong>{cleaned_query}</strong>' in <strong>{language.upper()}</strong></p>
                            </div>""", unsafe_allow_html=True)
                        if not news_items:
                            st.warning("📭 No news found. Try a different search term.")
                        else:
                            texts_for_keywords = [(news.get("title","")+ " "+ str(news.get("description",""))) for news in news_items]

                            # --- KEYWORDS ---
                            try:
                                resp = requests.post("http://127.0.0.1:8000/extract_keywords", json=texts_for_keywords)
                                keywords_list = resp.json().get("keywords", []) if resp.status_code==200 else [[] for _ in news_items]
                            except:
                                keywords_list = [[] for _ in news_items]
                            # --- SENTIMENT ---
                            try:
                                sentiment_resp = requests.post("http://127.0.0.1:8000/analyze_sentiment", json=texts_for_keywords)
                                sentiment_list = sentiment_resp.json().get("sentiments", []) if sentiment_resp.status_code==200 else [{} for _ in news_items]
                            except:
                                sentiment_list = [{} for _ in news_items]
                            # --- NER ---
                            try:
                                ner_resp = requests.post("http://127.0.0.1:8000/extract_entities", json=texts_for_keywords)
                                entities_list = ner_resp.json().get("entities", []) if ner_resp.status_code == 200 else [[] for _ in news_items]
                            except:
                                entities_list = [[] for _ in news_items]

                            kidx = 0
                            for i in range(0, len(news_items), 3):
                                row_news = news_items[i:i+3]
                                cols = st.columns(3)
                                for col, news in zip(cols, row_news):
                                    with col:
                                        image_url = news.get("image") or news.get("image_url") or ""
                                        title = news.get('title','No Title').replace("'", "&#39;").replace('"', '&quot;')
                                        source = news.get('source','Unknown').replace("'","&#39;")
                                        published = news.get('publishedAt','N/A')
                                        if published != 'N/A':
                                            try:
                                                from dateutil import parser
                                                dt = parser.parse(published)
                                                published = dt.strftime('%b %d, %Y %H:%M')
                                            except:
                                                pass
                                        description = news.get('description','No description available')[:200].replace("'", "&#39;").replace('"', '&quot;')
                                        url = news.get('url','#')
                                        keywords = keywords_list[kidx] if kidx < len(keywords_list) else []
                                        sentiment = sentiment_list[kidx] if kidx < len(sentiment_list) else []

                                        # --- ENTITY DISPLAY ---
                                        entities = entities_list[kidx] if kidx < len(entities_list) else []
                                        if entities:
                                            entities_html = (
                                                "<div style='margin-top:6px; margin-bottom:2px;'>"
                                                + " ".join(
                                                    f"<span style='background:{COLORS['light_gray']}40;color:{COLORS['medium_dark_gray']};padding:2px 6px; border-radius:5px; margin-right:3px; font-size:12px;'>{e.get('word','')} <span style='color:{COLORS['medium_gray']};font-size:11px;'>[{e.get('entity_group','')}]</span></span>"
                                                    for e in entities)
                                                + "</div>")
                                        else:
                                            entities_html = f"<div style='margin-top:6px; font-size:12px; color:{COLORS['light_medium_gray']};'>No entities</div>"

                                        if image_url:
                                            image_html = (
                                                '<div style="width:100%;height:150px;overflow:hidden;border-radius:8px;'
                                                f'background:{COLORS["light_gray"]};display:flex;align-items:center;justify-content:center;'
                                                'margin-bottom:8px;">'
                                                f'<img src="{image_url}" style="width:auto;max-width:100%;max-height:140px;object-fit:contain;"/>'
                                                '</div>')
                                        else:
                                            image_html = f'<div style="height:150px;display:flex;align-items:center;justify-content:center;font-size:34px;background:{COLORS["light_gray"]};border-radius:8px;margin-bottom:8px;">📰</div>'
                                        h3_style = f"font-size:1.14rem;font-weight:600;margin-bottom:7px;margin-top:2px;color:{COLORS['dark_bg']};line-height:1.3;"
                                        title_html = f'<h3 style="{h3_style}">{title}</h3>'
                                        if keywords:
                                            keywords_html = (
                                                "<div style='margin-top:6px; margin-bottom:2px;'>"
                                                + " ".join(
                                                    f"<span style='background:{COLORS['light_gray']}20;color:{COLORS['medium_gray']};padding:2px 6px; border-radius:5px; margin-right:3px; font-size:12px;'>{k}</span>" for k in keywords)
                                                + "</div>")
                                        else:
                                            keywords_html = f"<div style='margin-top:6px; font-size:12px; color:{COLORS['light_medium_gray']};'>No keywords</div>"
                                        sentiment_emojis = {
                                            "positive": "😊",
                                            "negative": "😞",
                                            "neutral": "😐"
                                        }
                                        sentiment_html = f"<div style='margin-top:10px; margin-bottom:4px; font-size:14px; color:{COLORS['dark_bg']};'>"
                                        if sentiment:
                                            label = sentiment.get('label','').lower()
                                            score = sentiment.get('score',0)
                                            emoji = sentiment_emojis.get(label,"🙂")
                                            label_cap = label.capitalize()
                                            sentiment_html += f"{emoji} <span style='font-weight:500;'>Sentiment:</span> <strong>{label_cap}</strong> <span style='font-size:12px; color:{COLORS['medium_dark_gray']};'>(confidence: {score:.2f})</span>"
                                        else:
                                            emoji = "🙂"
                                            sentiment_html += f"{emoji} Sentiment: N/A"
                                        sentiment_html += "</div>"
                                        kidx += 1
                                        card_style = (
                                            f"padding:16px; background:{COLORS['off_white']}; border-radius:10px; "
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
                        st.error("⚠️ Backend error. Please try again later.")
                except requests.exceptions.RequestException:
                    st.error("⚠️ Could not connect to backend. Make sure it is running.")


# ---------------------------------------------------------------------------
# App Logic
# ---------------------------------------------------------------------------
st.set_page_config(page_title="Neura News", layout="wide", page_icon="📰")

# Initialize session state
if "logged_in" not in st.session_state: st.session_state["logged_in"] = False
if "username" not in st.session_state: st.session_state["username"] = ""
if "show_login" not in st.session_state: st.session_state["show_login"] = True
if "current_page" not in st.session_state: st.session_state["current_page"] = "Dashboard"

# Show login/register or correct page
if not st.session_state["logged_in"]:
    if st.session_state["show_login"]:
        login()
    else:
        register()
else:
    if st.session_state.get("current_page") == "Profile":
        profile_management()
    else:
        news_dashboard()
