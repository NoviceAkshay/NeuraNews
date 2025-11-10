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
def _first(q, key, default=None):
    vals = q.get(key)
    if not vals:  # None or []
        return default
    return vals[0] if len(vals) > 0 else default

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

    # Read initial state from URL (shareable)
    q = st.query_params  # dict-like, values may be [], [""] or ["val"]
    # Days
    q_days_raw = _first(q, "days", 30)
    try:
        q_days = int(q_days_raw) if q_days_raw is not None else 30
    except Exception:
        q_days = 30

    # Other params (safe when list is empty or key missing)
    q_topic    = _first(q, "topic", "") or ""
    q_mode     = _first(q, "mode", "Heatmap") or "Heatmap"
    q_renderer = _first(q, "renderer", "deck.gl") or "deck.gl"
    q_country  = _first(q, "country", "") or ""

    # Controls
    days = st.slider("Window (days)", 7, 180, q_days, key="geo_days")

    topics = load_topics(days)
    topic_choices = ["All topics"] + topics

    # Preselect topic if present and valid
    if q_topic and q_topic in topics:
        topic_idx = topic_choices.index(q_topic) if q_topic in topic_choices else 0
    else:
        topic_idx = 0

    choice = st.selectbox("Topic", topic_choices, index=topic_idx, key="geo_topic")
    topic = None if choice == "All topics" else choice

    mode = st.radio(
        "Layer",
        ["Heatmap", "Points", "Hex bins"],
        horizontal=True,
        index=(["Heatmap", "Points", "Hex bins"].index(q_mode)
               if q_mode in ["Heatmap", "Points", "Hex bins"] else 0),
        key="geo_mode",
    )
    renderer = st.radio(
        "Renderer",
        ["deck.gl", "folium", "plotly"],
        horizontal=True,
        index=(["deck.gl", "folium", "plotly"].index(q_renderer)
               if q_renderer in ["deck.gl", "folium", "plotly"] else 0),
        key="geo_renderer",
    )

    # Optionally persist normalized params back to the URL so sharing is stable
    st.query_params = {
        "days": str(days),
        "topic": topic or "",
        "mode": mode,
        "renderer": renderer,
        "country": q_country or "",
    }

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
    for c in ["lat", "lon"]:
        if c not in df.columns:
            st.error(f"Missing column: {c}"); return
    if "weight" not in df.columns: df["weight"] = 1.0
    if "topic" not in df.columns: df["topic"] = "Unlabeled"
    if "date" not in df.columns: df["date"] = ""
    # optional title for heuristic fallback
    if "title" not in df.columns: df["title"] = ""

    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
    df = df.dropna(subset=["lat", "lon"])

    # Heuristic fallback topic for unlabeled rows (keeps "Unlabeled" if no match)
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

    # Country filter (coarse buckets; replace with reverse geocode later)
    def _bucket_country(lat, lon):
        if 5 <= lat <= 37 and 68 <= lon <= 97: return "India"
        if 24 <= lat <= 49 and -125 <= lon <= -66: return "USA"
        if 35 <= lat <= 72 and -10 <= lon <= 40: return "Europe"
        if -45 <= lat <= -10 and -75 <= lon <= -34: return "Brazil"
        return "Other"
    df["country"] = df.apply(lambda r: _bucket_country(float(r["lat"]), float(r["lon"])), axis=1)
    countries = ["All"] + sorted(df["country"].unique().tolist())
    country_idx = countries.index(q_country) if q_country and q_country in countries else 0
    country = st.selectbox("Country", countries, index=country_idx, key="geo_country")
    if country != "All":
        df = df[df["country"] == country]

    # Shareable link button (writes URL params)
    if st.button("Copy view link", key="geo_share"):
        st.query_params.update(
            days=str(days),
            topic=topic or "",
            mode=mode,
            renderer=renderer,
            country=(country if country != "All" else "")
        )
        st.success("Link updated in the address bar.")

    # Preview
    with st.expander("Preview data"):
        st.dataframe(df.head(300))

    if df.empty:
        st.info("No mappable rows after filters."); return

    center_lat = float(df["lat"].mean())
    center_lon = float(df["lon"].mean())

    # -------- Renderer branches --------
    if renderer == "deck.gl":
        # Topic coloring with gray fallback
        palette = ["#ff6b6b","#4dabf7","#51cf66","#ffd43b","#845ef7","#22b8cf","#ffa94d","#94d82d"]
        topics_list = sorted(df["topic"].dropna().unique().tolist())
        topic_colors = {t: [int(c[1:3],16),int(c[3:5],16),int(c[5:7],16),180] for t,c in zip(topics_list, palette*10)}
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

        # Mini details pane (nearest-by-haversine)
        if mode == "Points":
            st.subheader("Explore a location")
            lat_pick = st.number_input("Lat", value=center_lat, format="%.6f", key="geo_pick_lat")
            lon_pick = st.number_input("Lon", value=center_lon, format="%.6f", key="geo_pick_lon")
            radius_km = st.slider("Radius (km)", 10, 300, 50, key="geo_pick_radius")

            import numpy as np
            R = 6371.0
            lat1 = np.radians(lat_pick)
            lon1 = np.radians(lon_pick)
            lat2 = np.radians(df["lat"].astype(float).values)
            lon2 = np.radians(df["lon"].astype(float).values)
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            a = np.sin(dlat/2)**2 + np.cos(lat1)*np.cos(lat2)*np.sin(dlon/2)**2
            d = 2*R*np.arcsin(np.sqrt(a))
            sub = df.loc[d <= radius_km].copy()
            st.caption(f"{len(sub)} articles within {radius_km} km")
            if not sub.empty:
                cols = [c for c in ["date","topic","title","lat","lon","country"] if c in sub.columns]
                st.dataframe(sub.sort_values("date", ascending=False)[cols].head(50))

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
            # Clustered markers with popup (top article per bin)
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
            hover_data={"date": True, "lat": False, "lon": False, "size": False, "country": True},
            projection="natural earth",
        )
        fig.update_geos(showcountries=True, showcoastlines=True, showland=True, fitbounds="locations")
        fig.update_layout(margin=dict(l=0, r=0, t=0, b=0), legend_title_text="Topic", height=600)
        st.plotly_chart(fig, use_container_width=True)
