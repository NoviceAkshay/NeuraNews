# streamlit-frontend/admin_app.py
import os
import requests
import streamlit as st
import pandas as pd

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

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
# API helpers
# ----------------------------------------------------------------------------
def api_get(path: str, token: str = ""):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        r = requests.get(f"{API_BASE}{path}", headers=headers, timeout=60)
    except requests.RequestException as e:
        st.error(f"GET {path} failed: {e}")
        return None
    if r.status_code != 200:
        try:
            st.error(f"{path} -> {r.status_code}: {r.json()}")
        except Exception:
            st.error(f"{path} -> {r.status_code}: {r.text}")
        return None
    return r.json()

def api_post(path: str, payload: dict, token: str = ""):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    headers["Content-Type"] = "application/json"
    try:
        r = requests.post(f"{API_BASE}{path}", json=payload, headers=headers, timeout=60)
    except requests.RequestException as e:
        st.error(f"POST {path} failed: {e}")
        return None
    if r.status_code != 200:
        try:
            st.error(f"{path} -> {r.status_code}: {r.json()}")
        except Exception:
            st.error(f"{path} -> {r.status_code}: {r.text}")
        return None
    return r.json()

def admin_login(identifier: str, password: str):
    return api_post("/admin/login", {"identifier": identifier, "password": password})

# ----------------------------------------------------------------------------
# Session guards
# ----------------------------------------------------------------------------
def guard_token() -> str:
    if "admin_token" not in st.session_state:
        st.session_state["admin_token"] = ""
    return st.session_state["admin_token"]

def guard_user() -> dict:
    if "admin_user" not in st.session_state:
        st.session_state["admin_user"] = {}
    return st.session_state["admin_user"]


# ----------------------------------------------------------------------------
# Pages
# ----------------------------------------------------------------------------
def page_login():
    st.title("Admin Login")

    # Warm-up backend/DB so first real POST is fast
    try:
        ok = requests.get(f"{API_BASE}/admin/health", timeout=10)
        ok.raise_for_status()
    except Exception as e:
        st.info("Warming up the backend... if it’s a cold start, try again in a few seconds.")




def admin_login(identifier: str, password: str):
    try:
        r = requests.post(
            f"{API_BASE}/admin/login",
            json={"identifier": identifier, "password": password},
            timeout=180  # increased from 60
        )
    except requests.Timeout:
        st.error("Login request timed out. Backend not reachable or DB cold start; retry after a few seconds.")
        return None
    except requests.RequestException as e:
        st.error(f"Login failed to send: {e}")
        return None

    if r.status_code != 200:
        try:
            st.error(f"Login failed: {r.status_code} - {r.json()}")
        except Exception:
            st.error(f"Login failed: {r.status_code} - {r.text}")
        return None
    return r.json()


def page_dashboard():
    token = guard_token()
    if not token:
        st.info("Please login as admin first.")
        page_login()
        return

    user = guard_user()
    st.sidebar.success(f"Admin: {user.get('username','unknown')}")
    st.title("Admin Dashboard")

    # Controls (single source of truth)
    with st.sidebar:
        days = st.slider("Window (days)", min_value=7, max_value=90, value=30, step=7)
        if st.button("Refresh"):
            st.session_state._admin_refresh = True
            safe_rerun()

    # Insights badges
    ins = api_get(f"/admin/insights?days={days}", token)
    if ins:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Window", f"{ins.get('window_days', days)} days")
        with c2:
            st.metric("Dominant sentiment", ins.get("dominant_sentiment") or "—")
        with c3:
            st.metric("Hot topic", ins.get("hot_topic") or "—")

    # Trend
    data = api_get(f"/admin/stats/trend?days={days}", token)
    if data:
        st.subheader("Sentiment distribution")
        sd = data.get("sentiment_distribution", {})
        if sd:
            sd_df = pd.DataFrame({"label": list(sd.keys()), "count": list(sd.values())})
            st.bar_chart(sd_df.set_index("label"))
        st.subheader("Topic/day points")
        pts = pd.DataFrame(data.get("points", []))
        if not pts.empty:
            st.dataframe(pts, use_container_width=True, height=280)

    # Top topics list
    top_topics = api_get(f"/admin/topics/summary?days={days}&limit=8", token)
    if top_topics:
        st.subheader("Top topics")
        for row in top_topics:
            st.write(f"- {row['topic']}: {row['count']}")

    st.subheader("Users")
    users = api_get("/admin/users", token)
    if users:
        st.dataframe(pd.DataFrame(users), use_container_width=True, height=260)

    if st.button("Logout", type="primary"):
        st.session_state["admin_token"] = ""
        st.session_state["admin_user"] = {}
        st.success("Logged out.")
        safe_rerun()

def main():
    # Optional health check (no auth)
    api_get("/admin/health")
    token = guard_token()
    if token:
        page_dashboard()
    else:
        page_login()

if __name__ == "__main__":
    main()
