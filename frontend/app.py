import streamlit as st
import requests
import sys
import os
import re
from streamlit_mic_recorder import speech_to_text
import speech_recognition as sr


# Add project root to sys.path
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from backend.auth_service import register_user, login_user

BACKEND_URL = "http://127.0.0.1:8000/news"

# ---------------------------------------------------------------------------
# Custom CSS Styling
# ---------------------------------------------------------------------------
def load_css():
    st.markdown("""
        <style>
        body { background-color: #1e1e2f; }
        .main { background-color: #121212; }
        [data-testid="stSidebar"] { background-color: #2c3e50; }
        .stButton>button { background-color: #17a2b8; color: white; border-radius: 8px; padding: 8px 20px; font-weight: 500; }
        .stButton>button:hover { background-color: #138496; }
        .dashboard-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; text-align: center; }
        .filter-section { background: #34495E; padding: 2px; border-radius: 12px; margin-bottom: 20px; }
        .news-card-content { background: white; border-radius: 12px; padding: 16px; margin-bottom: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); height: 520px; display: flex; flex-direction: column; }
        .news-card-content:hover { transform: translateY(-5px); box-shadow: 0 8px 18px rgba(0,0,0,0.2); }
        .news-image-container { width: 100%; height: 220px; overflow: hidden; border-radius: 8px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; }
        .news-image-container img, .news-image { width: 100%; height: 100%; object-fit: cover; border-radius: 8px; }
        .news-image-container.placeholder { background: linear-gradient(135deg, #667eea, #764ba2); color: white; font-size: 40px; }
        .news-title { font-size: 18px; font-weight: 600; color: #2c3e50; margin-top: 5px; margin-bottom: 6px; }
        .source-info { color: #7f8c8d; font-size: 14px; margin-bottom: 8px; }
        .news-desc { color: #444; line-height: 1.6; font-size: 15px; }
        .news-link { color: #2563eb; font-weight: 500; }
        </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Profile Management
# ---------------------------------------------------------------------------
def profile_management():
    st.title("👤 Profile Management")
    username = st.session_state.get("username", "")
    with st.form("profile_form"):
        language = st.selectbox("Preferred Language", ["en", "hi"], key="profile_lang")
        interests = st.multiselect("Interest Areas", ["Technology", "Economy", "Environment"])
        submitted = st.form_submit_button("Update Profile")
        if submitted:
            profile_data = {"language": language, "interests": ", ".join(interests)}
            response = requests.put(f"http://127.0.0.1:8000/user/profile/{username}", json=profile_data)
            if response.status_code == 200:
                st.success("Profile updated successfully")
            else:
                st.error("Could not update profile")

# ---------------------------------------------------------------------------
# Authentication Functions
# ---------------------------------------------------------------------------
def login():
    st.title("🔐 Login")
    with st.form("login_form"):
        identifier = st.text_input("Username or Email", key="login_user")  # now used for both
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



def is_valid_email(email):
    # Simple regex for email validation
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)

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
                    st.session_state["current_page"] = "Dashboard"
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
    # Available languages for UI and news content
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
            payload = {
                "email": email,
                "language": language,
                "interests": interests
            }
            put_resp = requests.put(
                f"http://127.0.0.1:8000/user/profile/{username}",
                json=payload
            )
            if put_resp.status_code == 200:
                st.session_state["lang"] = language  # Update UI language
                st.success("Profile updated successfully!")
            else:
                st.error(f"Failed to update profile: {put_resp.text}")

    # Navigation button
    if st.button("⬅️ Back to Dashboard"):
        st.session_state["current_page"] = "Dashboard"
        st.rerun()





# ---------------------------------------------------------------------------
# Sidebar Navigation
# ---------------------------------------------------------------------------
def sidebar_navigation():
    with st.sidebar:
        st.markdown("""
            <div style='text-align: center; padding: 20px 0; border-bottom: 1px solid #34495e;'>
                <h2 style='color: #ecf0f1; margin: 0;'>📰 News Hub</h2>
                <p style='color: #95a5a6; font-size: 12px; margin: 5px 0 0 0;'>Stay Informed</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("📊 Dashboard", use_container_width=True):
            st.session_state["current_page"] = "Dashboard"
            st.rerun()
        if st.button("👤 Profile", use_container_width=True):
            st.session_state["current_page"] = "Profile"
            st.rerun()
        st.markdown(f"""
            <div style='background: #34495e; padding: 10px; border-radius: 8px; margin-bottom: 10px; text-align: center;'>
                <p style='color: #ecf0f1; margin: 0; font-size: 14px;'>👤 {st.session_state['username']}</p>
            </div>
        """, unsafe_allow_html=True)
        if st.button("🚪 Logout", use_container_width=True):
            st.session_state["logged_in"] = False
            st.session_state["username"] = ""
            st.rerun()

# ---------------------------------------------------------------------------
# Dashboard Logic
# ---------------------------------------------------------------------------



def news_dashboard():
    load_css()
    sidebar_navigation()
    st.markdown("""
        <div class='dashboard-header'>
            <h1>📰 News Dashboard</h1>
            <p>Discover the latest news and insights</p>
        </div>
    """, unsafe_allow_html=True)
    st.markdown("<div class='filter-section'>", unsafe_allow_html=True)

    col1, col2, col3 = st.columns([3, 1, 1])

    with col3:
        language = st.selectbox(
            "Language",
            ["en", "hi", "fr", "es", "de", "zh"],
            index=0
        )

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
                    st.warning("Didn’t get any speech, please try again.")
                    st.session_state["last_voice_query"] = ""

        query = st.text_input("🔍 Search for news", value=st.session_state.get("last_voice_query", ""),
                              placeholder="Enter a topic or speak")

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
                    response = requests.get(
                        BACKEND_URL,
                        params={
                            "query": query,
                            "page_size": page_size,
                            "language": language
                        }
                    )
                    if response.status_code == 200:
                        data = response.json()
                        news_items = data.get("results", [])
                        cleaned_query = data.get("cleaned_query", query)
                        st.markdown(f"""
                            <div style='background: white; padding: 15px; border-radius: 8px; margin: 20px 0;'>
                                <p style='margin: 0; color: #2c3e50;'>Showing <strong>{len(news_items)}</strong> articles for '<strong>{cleaned_query}</strong>' in <strong>{language.upper()}</strong></p>
                            </div>
                        """, unsafe_allow_html=True)
                        if not news_items:
                            st.warning("📭 No news found. Try a different search term.")
                        else:
                            texts_for_keywords = [
                                (news.get("title", "") + " " + str(news.get("description", "")))
                                for news in news_items
                            ]
                            try:
                                resp = requests.post("http://127.0.0.1:8000/extract_keywords", json=texts_for_keywords)
                                if resp.status_code == 200:
                                    keywords_list = resp.json().get("keywords", [])
                                else:
                                    keywords_list = [[] for _ in news_items]
                            except Exception:
                                keywords_list = [[] for _ in news_items]
                            kidx = 0
                            for i in range(0, len(news_items), 3):
                                row_news = news_items[i:i + 3]
                                cols = st.columns(3)
                                for col, news in zip(cols, row_news):
                                    with col:
                                        # Normalize image field for both APIs
                                        image_url = news.get("image") or news.get("image_url") or ""
                                        title = news.get('title', 'No Title').replace("'", "&#39;").replace('"', '&quot;')
                                        source = news.get('source', 'Unknown').replace("'", "&#39;")
                                        published = news.get('publishedAt', 'N/A')
                                        if published != 'N/A':
                                            # Format datetime if possible
                                            try:
                                                from dateutil import parser
                                                dt = parser.parse(published)
                                                published = dt.strftime('%b %d, %Y %H:%M')
                                            except Exception:
                                                pass
                                        description = news.get('description', 'No description available')[:200].replace("'", "&#39;").replace('"', '&quot;')
                                        url = news.get('url', '#')
                                        keywords = keywords_list[kidx] if kidx < len(keywords_list) else []
                                        if keywords:
                                            keywords_html = (
                                                "<div style='margin-top:6px; margin-bottom:2px;'>"
                                                + " ".join(
                                                    f"<span style='background:#2563eb20;color:#2563eb;padding:2px 6px; border-radius:5px; margin-right:3px; font-size:12px;'>{k}</span>"
                                                    for k in keywords)
                                                + "</div>"
                                            )
                                        else:
                                            keywords_html = "<div style='margin-top:6px; font-size:12px; color: #aaa;'>No keywords</div>"
                                        kidx += 1
                                        if image_url:
                                            image_html = f'<div class="news-image-container"><img src="{image_url}" class="news-image"/></div>'
                                        else:
                                            image_html = '<div class="news-image-container placeholder">📰</div>'
                                        st.html(f"""
                                            <div class='news-card-content'>
                                                {image_html}
                                                <h3 class='news-title'>{title}</h3>
                                                <p class='source-info'>🏷️ {source} &nbsp; | &nbsp; 📅 {published}</p>
                                                <p class='news-desc'>{description}...</p>
                                                {keywords_html}
                                                <a href="{url}" target="_blank" class="news-link">🔗 Open Article</a>
                                            </div>
                                        """)
                    else:
                        st.error("⚠️ Backend error. Please try again later.")
                except requests.exceptions.RequestException:
                    st.error("⚠️ Could not connect to backend. Make sure it is running.")



# ---------------------------------------------------------------------------
# App Logic
# ---------------------------------------------------------------------------
st.set_page_config(page_title="News Dashboard", layout="wide", page_icon="📰")

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
