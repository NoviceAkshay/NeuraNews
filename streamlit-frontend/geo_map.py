# streamlit-frontend/geo_map.py

import os
import requests
import pandas as pd
import streamlit as st
import pydeck as pdk

# --- API base (secrets -> env -> default) ---
def _get_api_base():
    try:
        return st.secrets["API_BASE"]
    except Exception:
        return os.getenv("API_BASE", "http://127.0.0.1:8000")

API_BASE = _get_api_base()

# --- Safe map style: only uses Mapbox if token exists ---
def _map_style():
    token = None
    try:
        token = st.secrets.get("MAPBOX_TOKEN", None)
    except Exception:
        token = None
    if token:
        pdk.settings.mapbox_api_key = token
        return "mapbox://styles/mapbox/dark-v11"
    return None  # default style

# --- Small rerun helper ---
def _safe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        try:
            st.rerun()
        except Exception:
            st.session_state["force_refresh"] = st.session_state.get("force_refresh", 0) + 1

# --- Caches ---
@st.cache_data(ttl=300)
def load_topics(days: int = 30) -> list[str]:
    try:
        r = requests.get(f"{API_BASE}/analytics/trend_public", params={"days": days}, timeout=20)
        r.raise_for_status()
        df = pd.DataFrame(r.json())
        return sorted(df["topic"].dropna().unique().tolist()) if not df.empty else []
    except Exception:
        return []

@st.cache_data(ttl=300)
def load_points(days: int, topic: str | None) -> pd.DataFrame:
    params = {"days": days}
    if topic:
        params["topic"] = topic
    r = requests.get(f"{API_BASE}/geo/heat", params=params, timeout=30)
    r.raise_for_status()
    return pd.DataFrame(r.json())

# --- Page ---
def run():
    st.title("Geo Heatmap")

    # Sidebar nav
    with st.sidebar:
        if st.button("⬅ Back to Home", key="geo_back_home"):
            st.session_state.page = "news_dashboard"
            _safe_rerun()
        if st.button("♻️ Clear cache", key="geo_clear_cache"):
            load_topics.clear(); load_points.clear()
            st.success("Cache cleared."); _safe_rerun()

    # Controls
    days = st.slider("Window (days)", 7, 180, 30, key="geo_days")
    topics = load_topics(days)
    choice = st.selectbox("Topic", ["All topics"] + topics, index=0, key="geo_topic")
    topic = None if choice == "All topics" else choice

    mode = st.radio("Layer", ["Heatmap", "Points", "Hex bins"], horizontal=True, key="geo_mode")
    renderer = st.radio("Renderer", ["deck.gl", "folium", "plotly"], horizontal=True, key="geo_renderer")

    # Data
    try:
        with st.spinner("Loading map data..."):
            df = load_points(days, topic)
    except requests.HTTPError as e:
        st.error(f"Map data failed to load ({e.response.status_code})."); return
    except Exception as e:
        st.error(f"Map data failed to load: {e}"); return

    if df.empty:
        st.info("No geocoded articles in this window."); return

    # Normalize schema
    # Normalize schema
    for c in ["lat", "lon"]:
        if c not in df.columns:
            st.error(f"Missing column: {c}");
            return
    if "weight" not in df.columns: df["weight"] = 1.0
    if "topic" not in df.columns: df["topic"] = "Unlabeled"
    if "date" not in df.columns: df["date"] = ""

    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])

    # >>> INSERT HERE: client-side fallback topic label <<<
    if "title" in df.columns:
        def _fallback_topic(row):
            t = (row.get("topic") or "").strip()
            if t and t.lower() != "unlabeled":
                return t
            title = (row.get("title") or "").lower()
            if any(k in title for k in ["election", "vote", "campaign"]): return "Politics"
            if any(k in title for k in ["ai", "artificial intelligence", "machine learning"]): return "AI"
            if any(k in title for k in ["climate", "weather", "flood", "heatwave"]): return "Climate"
            if any(k in title for k in ["market", "stocks", "inflation", "economy"]): return "Economy"
            if any(k in title for k in ["conflict", "war", "attack", "strike"]): return "Conflict"
            return "Unlabeled"

        df["topic"] = df.apply(_fallback_topic, axis=1)

    with st.expander("Preview data"):
        st.dataframe(df.head(300))

    if df.empty:
        st.info("No mappable rows after cleaning."); return

    center_lat = float(df["lat"].mean())
    center_lon = float(df["lon"].mean())

    # -------- Renderer branches --------
    if renderer == "deck.gl":
        # Optional topic coloring
        # Optional topic coloring
        palette = ["#ff6b6b", "#4dabf7", "#51cf66", "#ffd43b", "#845ef7", "#22b8cf", "#ffa94d", "#94d82d"]
        topics_list = topics or []
        topic_colors = {t: [int(c[1:3], 16), int(c[3:5], 16), int(c[5:7], 16), 180] for t, c in
                        zip(topics_list, palette * 10)}
        df["topic_color"] = df["topic"].apply(lambda t: topic_colors.get(t, [200, 200, 200, 160]))

        view = pdk.ViewState(latitude=center_lat, longitude=center_lon, zoom=3)

        if mode == "Heatmap":
            layers = [pdk.Layer("HeatmapLayer", data=df, get_position="[lon, lat]", get_weight="weight", radiusPixels=40)]
            tooltip = None
        elif mode == "Points":
            layers = [pdk.Layer("ScatterplotLayer", data=df, get_position="[lon, lat]",
                                get_radius=25000, get_fill_color="topic_color", pickable=True)]
            tooltip = {"text": "{topic}\n{date}"}
        else:
            layers = [pdk.Layer("HexagonLayer", data=df, get_position="[lon, lat]",
                                radius=30000, elevation_scale=20, extruded=True, coverage=1, pickable=True)]
            tooltip = {"html": "<b>Articles</b>: {elevationValue}"}

        st.pydeck_chart(pdk.Deck(layers=layers, initial_view_state=view, map_style=_map_style(), tooltip=tooltip))

    elif renderer == "folium":
        try:
            import folium
            from folium.plugins import HeatMap, MarkerCluster
            from streamlit_folium import st_folium
        except Exception as e:
            st.error(f"Folium not installed: {e}. Try: pip install folium streamlit-folium"); return

        tiles_choice = st.selectbox("Basemap (Folium)",
                                    ["CartoDB positron", "OpenStreetMap", "Stamen Toner"],
                                    index=0, key="folium_tiles")

        if tiles_choice == "Stamen Toner":
            m = folium.Map(
                location=[center_lat, center_lon],
                tiles="https://stamen-tiles.a.ssl.fastly.net/toner/{z}/{x}/{y}.png",
                attr="Map tiles by Stamen Design, under CC BY 3.0. Data by OpenStreetMap, under ODbL.",
                zoom_start=3, control_scale=True,
            )
        else:
            m = folium.Map(location=[center_lat, center_lon], tiles=tiles_choice, zoom_start=3, control_scale=True)

        if mode == "Heatmap":
            HeatMap(df[["lat","lon","weight"]].values.tolist(), radius=18, blur=15, max_zoom=6).add_to(m)
        elif mode == "Points":
            # Clustered markers with popup
            df_bin = df.copy()
            df_bin["lat_r"] = df_bin["lat"].round(2)
            df_bin["lon_r"] = df_bin["lon"].round(2)
            cluster = MarkerCluster().add_to(m)
            for _, r in df_bin.groupby(["lat_r","lon_r"]).agg({"topic":"first","date":"max"}).reset_index().iterrows():
                folium.CircleMarker(
                    location=[float(r["lat_r"]), float(r["lon_r"])],
                    radius=7, color="#ff8c00", fill=True, fill_opacity=0.7,
                    popup=f"{r['topic']} • {r['date']}",
                ).add_to(cluster)
        else:
            cluster = MarkerCluster().add_to(m)
            for _, r in df.iterrows():
                folium.CircleMarker(location=[float(r["lat"]), float(r["lon"])],
                                    radius=4, color="#99a", fill=True, fill_opacity=0.6).add_to(cluster)

        st_folium(m, height=600, width=None)

    else:  # Plotly
        try:
            import plotly.express as px
        except Exception as e:
            st.error(f"Plotly not installed: {e}. Try: pip install plotly"); return

        if mode != "Points":
            st.info("Plotly supports Points mode; switching to Points.")
            mode = "Points"

        df_plot = df.copy()
        df_plot["size"] = (df_plot["weight"].fillna(1.0) * 8).clip(4, 20)

        fig = px.scatter_geo(
            df_plot,
            lat="lat", lon="lon",
            color="topic",
            size="size",
            hover_name="topic",
            hover_data={"date": True, "lat": False, "lon": False, "size": False},
            projection="natural earth",
        )
        fig.update_geos(showcountries=True, showcoastlines=True, showland=True, fitbounds="locations")
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend_title_text="Topic", height=600)
        st.plotly_chart(fig, use_container_width=True)
