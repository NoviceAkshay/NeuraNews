# streamlit-frontend/time_series.py
import os
import requests
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# --- API base (secrets -> env -> default) ---
def _get_api_base():
    try:
        return st.secrets["API_BASE"]
    except Exception:
        return os.getenv("API_BASE", "http://127.0.0.1:8000")

API_BASE = _get_api_base()

# --- Helpers ---
def _safe_rerun():
    try:
        st.experimental_rerun()
    except Exception:
        try:
            st.rerun()
        except Exception:
            st.session_state["force_refresh"] = st.session_state.get("force_refresh", 0) + 1

@st.cache_data(ttl=300)
def load_trend(days: int, topic: str | None):
    params = {"days": days}
    if topic:
        params["topic"] = topic
    r = requests.get(f"{API_BASE}/analytics/trend_public", params=params, timeout=30)
    r.raise_for_status()
    df = pd.DataFrame(r.json())
    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])
    return df

@st.cache_data(ttl=300)
def load_topics(days: int = 30) -> list[str]:
    try:
        df = load_trend(days, None)
        if df.empty:
            return []
        return sorted(df["topic"].dropna().unique().tolist())
    except Exception:
        return []

def aggregate_df(df: pd.DataFrame, granularity: str) -> pd.DataFrame:
    if df.empty:
        return df
    if granularity == "Weekly":
        bucket = df["date"].dt.to_period("W").apply(lambda p: p.start_time)
    elif granularity == "Monthly":
        bucket = df["date"].dt.to_period("M").apply(lambda p: p.start_time)
    else:
        bucket = df["date"].dt.floor("D")
    out = (
        df.assign(bucket=bucket)
          .groupby(["bucket", "topic"], as_index=False)
          .agg(topic_count=("topic_count", "sum"),
               avg_sentiment=("avg_sentiment", "mean"))
          .rename(columns={"bucket": "date"})
          .sort_values("date")
    )
    return out

# --- Controls (inside run(), near other inputs) ---
# chart_type = st.radio("Chart type", ["Lines", "Bars", "Pie"], horizontal=True)

# --- Plotting (replace your plot_lines with this version) ---
def plot_lines(df: pd.DataFrame, topic: str | None, granularity: str, smooth: bool, top_n: int, chart_type: str):
    df = aggregate_df(df, granularity)
    has_classes = all(c in df.columns for c in ["pos_count","neg_count","neu_count"])

    if topic:
        st.subheader(f"Time Series — {topic} ({granularity})")
        ts = df[df["topic"] == topic].sort_values("date")
        if ts.empty:
            st.info("No data for the selected topic in this window.")
            return

        if chart_type == "Pie":
            if not has_classes:
                st.info("Class counts (pos/neg/neu) not available from API.")
                return
            totals = {
                "Positive": int(ts["pos_count"].sum()),
                "Negative": int(ts["neg_count"].sum()),
                "Neutral": int(ts["neu_count"].sum()),
            }
            fig, ax = plt.subplots()
            ax.pie(
                list(totals.values()),
                labels=list(totals.keys()),
                autopct="%1.1f%%",
                colors=["#2ca02c", "#ff7f0e", "#7f7f7f"],
                startangle=90,
            )
            ax.set_title(f"{topic}: Sentiment Share ({granularity} window)")
            st.pyplot(fig)
            return

        if chart_type == "Bars":
            fig, ax = plt.subplots()
            if has_classes:
                # stacked bars by date
                width = 0.8
                ax.bar(ts["date"], ts["pos_count"], width, label="Positive", color="#2ca02c")
                ax.bar(ts["date"], ts["neg_count"], width, bottom=ts["pos_count"], label="Negative", color="#ff7f0e")
                ax.bar(
                    ts["date"], ts["neu_count"], width,
                    bottom=ts["pos_count"] + ts["neg_count"], label="Neutral", color="#7f7f7f"
                )
                ax.set_ylabel("Articles")
                ax.set_title(f"{topic}: Daily Sentiment Counts")
                plt.xticks(rotation=45)
                ax.legend()
                st.pyplot(fig)
            else:
                # fall back: articles per day
                ax.bar(ts["date"], ts["topic_count"], color="tab:blue", label="Articles")
                ax.set_ylabel("Articles")
                ax.set_title(f"{topic}: Daily Articles")
                plt.xticks(rotation=45)
                ax.legend()
                st.pyplot(fig)
            return

        # Lines (default): articles + avg sentiment (and optional MAs)
        fig, ax = plt.subplots()
        ax.plot(ts["date"], ts["topic_count"], color="tab:blue", label="Articles")
        if smooth:
            win = 7 if granularity == "Daily" else (4 if granularity == "Weekly" else 3)
            ts["count_ma"] = ts["topic_count"].rolling(win, min_periods=1).mean()
            ax.plot(ts["date"], ts["count_ma"], color="tab:blue", linestyle="--", alpha=0.6, label=f"Articles ({win} MA)")
        ax.set_ylabel("Articles")

        ax2 = ax.twinx()
        ax2.plot(ts["date"], ts["avg_sentiment"], color="tab:red", label="Avg Sentiment")
        if smooth:
            win_s = 7 if granularity == "Daily" else (4 if granularity == "Weekly" else 3)
            ts["sent_ma"] = ts["avg_sentiment"].rolling(win_s, min_periods=1).mean()
            ax2.plot(ts["date"], ts["sent_ma"], color="tab:red", linestyle="--", alpha=0.6, label=f"Sentiment ({win_s} MA)")

        # optional class lines when present
        if has_classes:
            ax2.plot(ts["date"], ts["pos_count"], color="#2ca02c", label="Positive")
            ax2.plot(ts["date"], ts["neg_count"], color="#ff7f0e", label="Negative")
            ax2.plot(ts["date"], ts["neu_count"], color="#7f7f7f", label="Neutral")

        ax.set_title("Articles and Sentiment")
        ax2.set_ylabel("Sentiment / counts")
        plt.xticks(rotation=45)
        lines, labels = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines + lines2, labels + labels2, loc="upper left")
        st.pyplot(fig)
        return

    # All-topics view
    st.subheader(f"Time Series — Top {top_n} Topics ({granularity})")
    if df.empty:
        st.info("No data for this window.")
        return

    order = (
        df.groupby("topic")["topic_count"]
          .sum()
          .sort_values(ascending=False)
          .head(top_n)
          .index
    )
    if chart_type == "Bars" and has_classes:
        # stacked bars per topic using totals across the window
        totals = (
            df[df["topic"].isin(order)]
            .groupby("topic", as_index=False)
            .agg(pos=("pos_count","sum"), neg=("neg_count","sum"), neu=("neu_count","sum"))
            .set_index("topic")
        )
        fig, ax = plt.subplots()
        ax.bar(totals.index, totals["pos"], label="Positive", color="#2ca02c")
        ax.bar(totals.index, totals["neg"], bottom=totals["pos"], label="Negative", color="#ff7f0e")
        ax.bar(totals.index, totals["neu"], bottom=totals["pos"]+totals["neg"], label="Neutral", color="#7f7f7f")
        ax.set_ylabel("Articles")
        ax.set_title("Sentiment Counts by Topic")
        plt.xticks(rotation=45)
        ax.legend()
        st.pyplot(fig)
        return

    # fallback: small multiples (articles per topic)
    for t in order:
        g = df[df["topic"] == t].sort_values("date")
        fig, ax = plt.subplots()
        if chart_type == "Bars":
            ax.bar(g["date"], g["topic_count"], label=f"{t} count", color="tab:blue")
        else:
            ax.plot(g["date"], g["topic_count"], label=f"{t} count", color="tab:blue")
        ax.set_title(f"{t}: {granularity} Articles")
        ax.set_xlabel("Date")
        ax.set_ylabel("Count")
        ax.legend()
        plt.xticks(rotation=45)
        st.pyplot(fig)


def run():
    st.title("News Trends")

    with st.sidebar:
        if st.button("⬅ Back to Home", key="ts_back_sidebar"):
            st.session_state.page = "news_dashboard"
            _safe_rerun()
        if st.button("♻️ Clear cache"):
            load_trend.clear()
            load_topics.clear()
            st.success("Cache cleared.")
            _safe_rerun()

    if st.button("⬅ Back"):
        st.session_state.page = "news_dashboard"
        _safe_rerun()

    st.caption(f"API: {API_BASE}")

    # Controls
    days = st.slider("Window (days)", 7, 180, 30)
    topics = load_topics(days=days)
    chart_type = st.radio("Chart type", ["Lines", "Bars", "Pie"], horizontal=True)
    choice = st.selectbox("Topic", ["All topics"] + topics, index=0)
    topic = None if choice == "All topics" else choice
    granularity = st.radio("Granularity", ["Daily", "Weekly", "Monthly"], horizontal=True, index=0)
    smooth = st.checkbox("Show moving average", value=True)
    top_n = st.number_input("Top N topics to display (All topics view)", min_value=1, max_value=15, value=6, step=1)

    # Fetch after controls so UI always renders
    try:
        with st.spinner("Loading trends..."):
            df = load_trend(days, topic)
    except requests.HTTPError as e:
        st.error(f"Failed to load trends ({e.response.status_code}). Open {API_BASE}/analytics/trend_public?days={days} in a browser to inspect the backend error.")
        return
    except Exception as e:
        st.error(f"Failed to load trends: {e}")
        return

    # Preview to verify variation
    with st.expander("Preview data"):
        if df.empty:
            st.write("No rows.")
        else:
            st.dataframe(df.sort_values(["topic", "date"]).head(200))

    # Plot
    plot_lines(df, topic, granularity, smooth, top_n, chart_type)


with st.sidebar:
    if st.button("⬅ Back to Home", key="back_home_sidebar_ts"):  # use unique keys per page
        st.session_state.page = "news_dashboard"
        _safe_rerun()
if st.button("⬅ Back"):
    st.session_state.page = "news_dashboard"
    _safe_rerun()


if __name__ == "__main__":
    run()
