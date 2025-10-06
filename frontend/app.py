import streamlit as st
import requests

import sys
import os

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
        [data-testid="stSidebar"] { background-color: #2c3e50; display: flex; flex-direction: column; justify-content: space-between; }
        .stButton>button { background-color: #17a2b8; color: w  hite; border-radius: 8px; border: none; padding: 8px 20px; font-weight: 500; transition: background-color 0.2s ease; }
        .stButton>button:hover { background-color: #138496; }
        .dashboard-header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; border-radius: 12px; margin-bottom: 30px; text-align: center; }
        .filter-section { background: #34495E; padding: 2px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); }
        .news-card-content { background: white; border-radius: 12px; padding: 16px; margin-bottom: 24px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); transition: transform 0.25s ease, box-shadow 0.25s ease; height: 520px; display: flex; flex-direction: column; justify-content: flex-start; }
        .news-card-content:hover { transform: translateY(-5px); box-shadow: 0 8px 18px rgba(0,0,0,0.2); }
        .news-image-container { width: 100%; height: 220px; overflow: hidden; border-radius: 8px; background: #f0f0f0; display: flex; align-items: center; justify-content: center; }
        .news-image-container img, .news-image { width: 100%; height: 100%; object-fit: cover; border-radius: 8px; }
        .news-image-container.placeholder { background: linear-gradient(135deg, #667eea, #764ba2); color: white; font-size: 40px; }
        .news-title { font-size: 18px; font-weight: 600; color: #2c3e50; margin-top: 5px; margin-bottom: 6px; }
        .source-info { color: #7f8c8d; font-size: 14px; margin-bottom: 8px; }
        .news-desc { color: #444; line-height: 1.6; font-size: 15px; flex-grow: 1; }
        .news-link { display: inline-block; margin-top: 10px; color: #2563eb; text-decoration: none; font-weight: 500; }
        .news-link:hover { text-decoration: underline; }
        @media (max-width: 1200px) { .news-card-content { height: 500px; } }
        @media (max-width: 900px) { .stColumn { flex: 0 0 48% !important; max-width: 48% !important; } }
        @media (max-width: 600px) { .stColumn { flex: 0 0 100% !important; max-width: 100% !important; } }
        </style>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# User Functions
# ---------------------------------------------------------------------------


def login():
    st.title("🔐 Login")
    with st.form("login_form"):
        username = st.text_input("Username", key="login_user")
        password = st.text_input("Password", type="password", key="login_pass")
        submitted = st.form_submit_button("Login")

        if submitted:
            success, user = login_user(username, password)
            if success:
                st.session_state["logged_in"] = True
                st.session_state["username"] = user.username
                st.success(f"Welcome, {user.username}!")
                st.session_state["current_page"] = "Dashboard"
            else:
                st.error("Incorrect username or password")

    if st.button("Go to Registration"):
        st.session_state["show_login"] = False


def register():
    st.title("📝 Register")
    with st.form("register_form"):
        username = st.text_input("Choose a username", key="reg_user")
        password = st.text_input("Choose a password", type="password", key="reg_pass")
        confirm = st.text_input("Confirm password", type="password", key="reg_confirm")
        submitted = st.form_submit_button("Register")

        if submitted:
            if not username or not password or not confirm:
                st.warning("All fields are required")
            elif password != confirm:
                st.warning("Passwords do not match")
            else:
                success, message = register_user(username, password)
                if success:
                    st.success(message)
                    st.session_state["show_login"] = True
                    st.session_state["current_page"] = "Dashboard"
                else:
                    st.error(message)

    if st.button("Back to Login"):
        st.session_state["show_login"] = True




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

        st.markdown("<div style='flex-grow: 1;'></div>", unsafe_allow_html=True)  # Push footer down

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
# Dashboard
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
    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input("🔍 Search for news", "", placeholder="Enter a topic...")
    with col2:
        page_size = st.selectbox("Articles", [5, 10, 15, 20], index=0)
    search_button = st.button("🔎 Search News", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    if search_button:
        if not query.strip():
            st.warning("⚠️ Please enter a search term")
        else:
            with st.spinner("🔄 Fetching latest news..."):
                try:
                    response = requests.get(BACKEND_URL, params={"query": query, "page_size": page_size})
                    if response.status_code == 200:
                        data = response.json()
                        news_items = data.get("results", [])
                        cleaned_query = data.get("cleaned_query", query)

                        st.markdown(f"""
                            <div style='background: white; padding: 15px; border-radius: 8px; margin: 20px 0;'>
                                <p style='margin: 0; color: #2c3e50;'>Showing <strong>{len(news_items)}</strong> articles for '<strong>{cleaned_query}</strong>'</p>
                            </div>
                        """, unsafe_allow_html=True)

                        if not news_items:
                            st.warning("📭 No news found. Try a different search term.")
                        else:
                            for i in range(0, len(news_items), 3):
                                row_news = news_items[i:i + 3]
                                cols = st.columns(3)
                                for col, news in zip(cols, row_news):
                                    with col:
                                        image_url = news.get("image", "")
                                        title = news.get('title', 'No Title').replace("'", "&#39;").replace('"', '&quot;')
                                        source = news.get('source', 'Unknown').replace("'", "&#39;")
                                        published = news.get('publishedAt', 'N/A')
                                        description = news.get('description', 'No description available')[:200].replace("'", "&#39;").replace('"', '&quot;')
                                        url = news.get('url', '#')

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
# if "user_db" not in st.session_state: st.session_state["user_db"] = {"guest": "guest123"}
if "current_page" not in st.session_state: st.session_state["current_page"] = "Dashboard"

# Show login/register or dashboard
if not st.session_state["logged_in"]:
    if st.session_state["show_login"]:
        login()
    else:
        register()
else:
    news_dashboard()
