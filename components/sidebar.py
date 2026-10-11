import streamlit as st

def render_sidebar():
    """Render the vertical sidebar navigation"""
    with st.sidebar:
        st.title("Navigation")
        
        # Navigation items
        home_selected = st.button("Home")
        dashboard_selected = st.button("Dashboard")
        
        # Return which page is selected
        return home_selected, dashboard_selected