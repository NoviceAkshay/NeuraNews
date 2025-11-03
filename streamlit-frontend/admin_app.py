# streamlit-frontend/admin_app.py
import os
import requests
import streamlit as st
import pandas as pd

API_BASE = os.getenv("API_BASE", "http://127.0.0.1:8000")

def api_get(path: str, token: str = ""):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    r = requests.get(f"{API_BASE}{path}", headers=headers, timeout=60)
    if r.status_code != 200:
        try:
            st.error(f"{path} -> {r.status_code}: {r.json()}")
        except Exception:
            st.error(f"{path} -> {r.status_code}: {r.text}")
        return None
    return r.json()

def admin_login(identifier: str, password: str):
    r = requests.post(f"{API_BASE}/admin/login", json={"identifier": identifier, "password": password}, timeout=60)
    if r.status_code != 200:
        try:
            st.error(f"Login failed: {r.status_code} - {r.json()}")
        except Exception:
            st.error(f"Login failed: {r.status_code} - {r.text}")
        return None
    return r.json()

def guard():
    if "admin_token" not in st.session_state:
        st.session_state["admin_token"] = ""
    return st.session_state["admin_token"]

def page_login():
    st.title("Admin Login")
    identifier = st.text_input("Username or Email")
    password = st.text_input("Password", type="password")
    if st.button("Login as Admin", use_container_width=True):
        res = admin_login(identifier, password)
        if res and res.get("token"):
            st.session_state["admin_token"] = res["token"]
            st.session_state["admin_user"] = {"username": res.get("username"), "email": res.get("email")}
            st.success("Logged in as admin.")
            st.rerun()

def page_dashboard():
    token = guard()
    if not token:
        st.info("Please login as admin first.")
        page_login()
        return
    st.sidebar.success(f"Admin: {st.session_state.get('admin_user',{}).get('username','unknown')}")
    st.title("Admin Dashboard")

    col1, col2 = st.columns(2)
    with col1:
        days = st.slider("Days", 7, 90, 30, 1)
    with col2:
        if st.button("Refresh"):
            st.rerun()

    data = api_get(f"/admin/stats/trend?days={days}", token)
    if data:
        st.subheader("Sentiment distribution")
        sd = data.get("sentiment_distribution", {})
        sd_df = pd.DataFrame({"label": list(sd.keys()), "count": list(sd.values())})
        st.bar_chart(sd_df.set_index("label"))

        st.subheader("Topic/day points")
        pts = pd.DataFrame(data.get("points", []))
        if not pts.empty:
            st.dataframe(pts)

    st.subheader("Users")
    users = api_get("/admin/users", token)
    if users:
        st.dataframe(pd.DataFrame(users))

    if st.button("Logout", type="primary"):
        st.session_state["admin_token"] = ""
        st.session_state["admin_user"] = {}
        st.success("Logged out.")
        st.rerun()

def main():
    # Optional health check
    api_get("/admin/health")
    token = guard()
    if token:
        page_dashboard()
    else:
        page_login()

if __name__ == "__main__":
    main()
