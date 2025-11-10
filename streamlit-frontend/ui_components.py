import streamlit as st

def show_success_message(message: str, icon: str = "✅"):
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
                    border: 1px solid #10b981; border-radius: 12px;
                    padding: 1rem; margin: 1rem 0; display: flex; align-items: center; gap: 12px;
                    animation: slideIn 0.3s ease-out;'>
            <span style='font-size: 1.5rem;'>{icon}</span>
            <span style='color: #065f46; font-weight: 500;'>{message}</span>
        </div>
        <style>
            @keyframes slideIn {{
                from {{ transform: translateX(-20px); opacity: 0; }}
                to {{ transform: translateX(0); opacity: 1; }}
            }}
        </style>
    """, unsafe_allow_html=True)

def show_error_message(message: str, icon: str = "❌"):
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
                    border: 1px solid #ef4444; border-radius: 12px;
                    padding: 1rem; margin: 1rem 0; display: flex; align-items: center; gap: 12px;
                    animation: slideIn 0.3s ease-out;'>
            <span style='font-size: 1.5rem;'>{icon}</span>
            <span style='color: #991b1b; font-weight: 500;'>{message}</span>
        </div>
    """, unsafe_allow_html=True)

def show_info_message(message: str, icon: str = "ℹ️"):
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
                    border: 1px solid #3b82f6; border-radius: 12px;
                    padding: 1rem; margin: 1rem 0; display: flex; align-items: center; gap: 12px;
                    animation: slideIn 0.3s ease-out;'>
            <span style='font-size: 1.5rem;'>{icon}</span>
            <span style='color: #1e40af; font-weight: 500;'>{message}</span>
        </div>
    """, unsafe_allow_html=True)

def show_warning_message(message: str, icon: str = "⚠️"):
    st.markdown(f"""
        <div style='background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
                    border: 1px solid #f59e0b; border-radius: 12px;
                    padding: 1rem; margin: 1rem 0; display: flex; align-items: center; gap: 12px;
                    animation: slideIn 0.3s ease-out;'>
            <span style='font-size: 1.5rem;'>{icon}</span>
            <span style='color: #92400e; font-weight: 500;'>{message}</span>
        </div>
    """, unsafe_allow_html=True)

def show_loading_spinner(message: str = "Loading..."):
    st.markdown(f"""
        <div style='text-align: center; padding: 2rem; background: white; border-radius: 16px;
                    border: 1px solid #e5e7eb; margin: 1rem 0;'>
            <div style='font-size: 2rem; margin-bottom: 1rem; animation: spin 1s linear infinite;'>🔄</div>
            <p style='color: #6b7280; font-weight: 500;'>{message}</p>
        </div>
        <style>
            @keyframes spin {{
                from {{ transform: rotate(0deg); }}
                to {{ transform: rotate(360deg); }}
            }}
        </style>
    """, unsafe_allow_html=True)

def show_empty_state(title: str = "No data available", description: str = "", icon: str = "📭", tip: str = ""):
    st.markdown(f"""
        <div style='background: white; border: 2px dashed #d1d5db; border-radius: 16px;
                    padding: 3rem 2rem; margin: 2rem 0; text-align: center;'>
            <div style='font-size: 4rem; margin-bottom: 1rem; opacity: 0.5;'>{icon}</div>
            <h3 style='color: #374151; margin-bottom: 0.5rem;'>{title}</h3>
            <p style='color: #6b7280; font-size: 0.95rem; margin-bottom: 1.5rem;'>{description}</p>
            {f"<div style='display: inline-block; background: #f3f4f6; padding: 0.75rem 1.5rem; border-radius: 8px; color: #4b5563; font-size: 0.9rem;'><strong>Tip:</strong> {tip}</div>" if tip else ""}
        </div>
    """, unsafe_allow_html=True)

def show_stat_card(label: str, value: str, icon: str = "📊", color: str = "#2563eb"):
    st.markdown(f"""
        <div style='background: white; border-radius: 16px; padding: 1.5rem;
                    border: 1px solid #e5e7eb; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
                    transition: all 0.3s ease;'
             onmouseover="this.style.transform='translateY(-4px)';this.style.boxShadow='0 8px 20px rgba(0,0,0,0.1)'"
             onmouseout="this.style.transform='translateY(0)';this.style.boxShadow='0 2px 8px rgba(0,0,0,0.05)'">
            <div style='display: flex; align-items: center; gap: 12px; margin-bottom: 8px;'>
                <span style='font-size: 2rem;'>{icon}</span>
                <span style='color: #6b7280; font-size: 0.9rem; font-weight: 500;'>{label}</span>
            </div>
            <div style='font-size: 2rem; font-weight: 700; color: {color};'>{value}</div>
        </div>
    """, unsafe_allow_html=True)

def show_progress_bar(progress: float, label: str = ""):
    st.markdown(f"""
        <div style='background: white; border-radius: 12px; padding: 1rem;
                    border: 1px solid #e5e7eb; margin: 1rem 0;'>
            {f"<p style='color: #374151; font-weight: 500; margin-bottom: 0.5rem;'>{label}</p>" if label else ""}
            <div style='width: 100%; height: 8px; background: #e5e7eb; border-radius: 4px; overflow: hidden;'>
                <div style='width: {progress}%; height: 100%;
                            background: linear-gradient(90deg, #2563eb 0%, #4338ca 100%);
                            transition: width 0.5s ease;'></div>
            </div>
            <p style='color: #6b7280; font-size: 0.85rem; margin-top: 0.5rem; text-align: right;'>{progress}%</p>
        </div>
    """, unsafe_allow_html=True)

def show_badge(text: str, color: str = "#2563eb", bg_color: str = "#dbeafe"):
    return f"""
        <span style='display: inline-block; background: {bg_color}; color: {color};
                     padding: 4px 12px; border-radius: 9999px; font-size: 0.85rem;
                     font-weight: 500; margin: 2px;'>
            {text}
        </span>
    """

def show_divider(text: str = ""):
    if text:
        st.markdown(f"""
            <div style='display: flex; align-items: center; margin: 2rem 0;'>
                <div style='flex: 1; height: 1px; background: #e5e7eb;'></div>
                <span style='padding: 0 1rem; color: #6b7280; font-weight: 500; font-size: 0.9rem;'>{text}</span>
                <div style='flex: 1; height: 1px; background: #e5e7eb;'></div>
            </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown("<div style='height: 2px; background: linear-gradient(90deg, transparent, #e5e7eb 50%, transparent); margin: 2rem 0;'></div>", unsafe_allow_html=True)
