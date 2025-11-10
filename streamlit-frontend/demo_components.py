"""
Demo page to showcase new UI components
Run with: streamlit run streamlit-frontend/demo_components.py
"""

import streamlit as st
from ui_components import (
    show_success_message,
    show_error_message,
    show_info_message,
    show_warning_message,
    show_loading_spinner,
    show_empty_state,
    show_stat_card,
    show_progress_bar,
    show_badge,
    show_divider,
)

st.set_page_config(page_title="UI Components Demo", page_icon="🎨", layout="wide")

st.title("🎨 Neura News UI Components Showcase")
st.markdown("Preview of all available UI components")

show_divider("Alert Messages")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Success Message")
    show_success_message("Your changes have been saved successfully!")

    st.subheader("Info Message")
    show_info_message("New features are available. Check them out!")

with col2:
    st.subheader("Error Message")
    show_error_message("Failed to connect to the server. Please try again.")

    st.subheader("Warning Message")
    show_warning_message("Your session will expire in 5 minutes.")

show_divider("Loading & Empty States")

col1, col2 = st.columns(2)

with col1:
    st.subheader("Loading Spinner")
    show_loading_spinner("Fetching latest news articles...")

with col2:
    st.subheader("Empty State")
    show_empty_state(
        title="No articles found",
        description="Try adjusting your search terms",
        icon="📰",
        tip="Use broader keywords or try a different language"
    )

show_divider("Statistics Cards")

st.subheader("Stat Cards")
col1, col2, col3, col4 = st.columns(4)

with col1:
    show_stat_card("Total Articles", "1,234", "📰", "#2563eb")

with col2:
    show_stat_card("Positive News", "856", "😊", "#10b981")

with col3:
    show_stat_card("Neutral News", "278", "😐", "#6b7280")

with col4:
    show_stat_card("Negative News", "100", "😞", "#ef4444")

show_divider("Progress Bars")

st.subheader("Progress Indicators")
show_progress_bar(75, "Article Processing")
show_progress_bar(45, "Sentiment Analysis")
show_progress_bar(90, "Entity Extraction")

show_divider("Badges")

st.subheader("Badge Components")
st.markdown(f"""
    <div style='background: white; padding: 1.5rem; border-radius: 12px; border: 1px solid #e5e7eb;'>
        <p style='color: #374151; margin-bottom: 1rem;'><strong>Categories:</strong></p>
        {show_badge("Technology", "#2563eb", "#dbeafe")}
        {show_badge("Politics", "#dc2626", "#fee2e2")}
        {show_badge("Sports", "#16a34a", "#dcfce7")}
        {show_badge("Entertainment", "#ca8a04", "#fef3c7")}
        {show_badge("Science", "#7c3aed", "#ede9fe")}
    </div>
""", unsafe_allow_html=True)

show_divider("Feature Cards")

st.subheader("Feature Cards")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown("""
        <div style='background: white; border-radius: 16px; padding: 1.5rem;
                    border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                    transition: all 0.3s ease; text-align: center;'
             onmouseover="this.style.transform='translateY(-4px)';this.style.boxShadow='0 8px 20px rgba(0,0,0,0.12)'"
             onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 2px 8px rgba(0,0,0,0.05)'">
            <div style='font-size: 3rem; margin-bottom: 1rem;'>🔎</div>
            <h4 style='color: #1a1a1a; margin-bottom: 0.5rem;'>Smart Search</h4>
            <p style='color: #6b7280; font-size: 0.9rem; line-height: 1.5;'>
                AI-powered search with advanced filters
            </p>
        </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown("""
        <div style='background: white; border-radius: 16px; padding: 1.5rem;
                    border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                    transition: all 0.3s ease; text-align: center;'
             onmouseover="this.style.transform='translateY(-4px)';this.style.boxShadow='0 8px 20px rgba(0,0,0,0.12)'"
             onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 2px 8px rgba(0,0,0,0.05)'">
            <div style='font-size: 3rem; margin-bottom: 1rem;'>💬</div>
            <h4 style='color: #1a1a1a; margin-bottom: 0.5rem;'>Sentiment Analysis</h4>
            <p style='color: #6b7280; font-size: 0.9rem; line-height: 1.5;'>
                Real-time sentiment and entity extraction
            </p>
        </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown("""
        <div style='background: white; border-radius: 16px; padding: 1.5rem;
                    border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                    transition: all 0.3s ease; text-align: center;'
             onmouseover="this.style.transform='translateY(-4px)';this.style.boxShadow='0 8px 20px rgba(0,0,0,0.12)'"
             onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 2px 8px rgba(0,0,0,0.05)'">
            <div style='font-size: 3rem; margin-bottom: 1rem;'>🎙️</div>
            <h4 style='color: #1a1a1a; margin-bottom: 0.5rem;'>Voice Search</h4>
            <p style='color: #6b7280; font-size: 0.9rem; line-height: 1.5;'>
                Hands-free news discovery
            </p>
        </div>
    """, unsafe_allow_html=True)

show_divider()

st.markdown("""
    <div style='text-align: center; padding: 2rem; background: linear-gradient(135deg, #667eea22 0%, #764ba222 100%);
                border-radius: 16px; margin-top: 2rem;'>
        <h3 style='color: #1a1a1a; margin-bottom: 0.5rem;'>Ready to use these components?</h3>
        <p style='color: #6b7280; font-size: 0.95rem;'>
            Import them from <code>ui_components.py</code> and start building!
        </p>
    </div>
""", unsafe_allow_html=True)
