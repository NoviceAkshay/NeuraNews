# streamlit-frontend/trend_insights.py
#
# import streamlit as st
# import pandas as pd
# import matplotlib.pyplot as plt
#
# def run_trend_insights(df):
#     st.title("Trend Insights")
#     st.header("Topic vs Sentiment Correlation")
#
#     # Correlation Calculation
#     correlation = df['sentiment'].corr(df['topic1_count'])
#     st.write(f"Pearson Correlation: {correlation:.3f}")
#
#     # Scatterplot Visualization
#     fig, ax = plt.subplots()
#     ax.scatter(df['topic1_count'], df['sentiment'])
#     ax.set_xlabel('Topic Frequency')
#     ax.set_ylabel('Sentiment Score')
#     ax.set_title('Sentiment vs Topic Frequency')
#     st.pyplot(fig)
#
#     # Add more trend/insight features here, e.g. spike detection, summary reports, etc.


# streamlit-frontend/trend_insights.py
# streamlit-frontend/trend_insights.py
import streamlit as st
import matplotlib.pyplot as plt
import pandas as pd

def run_trend_insights(df: pd.DataFrame):
    st.header("Topic vs Sentiment Correlation")
    if {"topic_count", "avg_sentiment"}.issubset(df.columns) and not df.empty:
        corr = df["avg_sentiment"].corr(df["topic_count"])
        st.write(f"Pearson Correlation: {corr:.3f}")
        fig, ax = plt.subplots()
        ax.scatter(df["topic_count"], df["avg_sentiment"], alpha=0.7)
        ax.set_xlabel("Topic Frequency")
        ax.set_ylabel("Avg Sentiment")
        ax.set_title("Sentiment vs Topic Frequency")
        st.pyplot(fig)
    else:
        st.info("Not enough data to compute trend insights.")
