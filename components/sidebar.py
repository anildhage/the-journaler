import streamlit as st
import os

def render_sidebar():
    """Render the vertical sidebar navigation"""
    with st.sidebar:
        st.title("Navigation")
        
        # Navigation items
        home_selected = st.button("Home")
        dashboard_selected = st.button("Dashboard")
        
        # Dynamically scan for organized folders
        organized_dir = "./organized"
        category_tabs = []
        
        if os.path.exists(organized_dir):
            try:
                # Get all subdirectories in organized folder
                for item in os.listdir(organized_dir):
                    item_path = os.path.join(organized_dir, item)
                    if os.path.isdir(item_path):
                        category_tabs.append(item)
            except Exception as e:
                st.error(f"Error scanning organized folders: {str(e)}")
        
        # Create buttons for each detected category
        category_selected = None
        for category in sorted(category_tabs):
            if st.button(f"📁 {category}"):
                category_selected = category
                
        # Return which page is selected
        return home_selected, dashboard_selected, category_selected