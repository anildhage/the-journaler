import streamlit as st
from components.sidebar import render_sidebar
from services.transcription_service import init_transcription_service
from services.config_service import load_settings, save_settings
import os
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="Journaler & Voice Hub",
    page_icon="🎤",
    layout="wide"
)

# Define directory paths directly (since we had import issues)
INBOX_DIR = "./inbox"
RAW_MARKDOWN_DIR = "./raw-markdown"

# Create directories if they don't exist
os.makedirs(INBOX_DIR, exist_ok=True)
os.makedirs(RAW_MARKDOWN_DIR, exist_ok=True)

# Set page configuration
st.set_page_config(
    page_title="Journaler & Voice Hub",
    page_icon="🎤",
    layout="wide"
)

# Initialize the transcription service (this will start in background)
transcription_service = init_transcription_service()

# Load settings from config service
settings = load_settings()

# Initialize session state variables for settings if not already present
if "whisper_model" not in st.session_state:
    st.session_state.whisper_model = settings["whisper_model"]

if "ollama_model" not in st.session_state:
    st.session_state.ollama_model = settings["ollama_model"]

# Default to Home view
if "current_view" not in st.session_state:
    st.session_state.current_view = "Home"

# Render sidebar
home_selected, dashboard_selected = render_sidebar()

# Update view based on sidebar selection
if home_selected:
    st.session_state.current_view = "Home"
elif dashboard_selected:
    st.session_state.current_view = "Dashboard"

# Main content area
st.title("Journaler & Voice Hub")

# Display current view
if st.session_state.current_view == "Home":
    # Home View
    st.header("Welcome to Journaler & Voice Hub")
    
    st.markdown("""
    This application is a voice-to-markdown processing hub and content dashboard.
    
    You can use it to:
    - Convert voice recordings to markdown format
    - Manage your journal entries
    - View system statistics and analytics
    """)
    
    # Show transcription service status
    st.subheader("System Status")
    status = transcription_service.get_status()
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric(label="Total Entries Processed", value=str(status["total_processed"]))
        
    with col2:
        st.metric(label="Processing Status", value=status["current_status"])
        
    with col3:
        st.metric(label="Pending Files", value=str(status["pending_files_count"]))

elif st.session_state.current_view == "Dashboard":
    # Dashboard View
    st.header("Dashboard")
    
    # Create sub-tabs for the dashboard
    tab1, tab2 = st.tabs(["Audio Processing Status", "System Analytics"])
    
    with tab1:
        st.subheader("Audio Processing Status")
        
        # Add settings controls at the top of this tab
        st.markdown("### Settings")
        
        # Load current configuration
        current_whisper_model = st.session_state.get('whisper_model', 'base')
        current_ollama_model = st.session_state.get('ollama_model', 'llama3:latest')
        
        # Create expandable section for model settings
        with st.expander("⚙️ Processing Settings & Model Selection"):
            # Whisper model selection
            whisper_model = st.selectbox(
                "Whisper Model (STT)",
                options=["tiny", "base", "small", "medium", "large"],
                index=["tiny", "base", "small", "medium", "large"].index(current_whisper_model),
                key="whisper_model_select"
            )
            
            # Ollama model selection
            ollama_model = st.selectbox(
                "Ollama Model (LLM)",
                options=["llama3-groq-tool-use:8b", "qwen2.5-coder:32b", "mistral:7b"],
                index=["llama3-groq-tool-use:8b", "qwen2.5-coder:32b", "mistral:7b"].index(current_ollama_model),
                key="ollama_model_select"
            )
            
            # Save settings button
            if st.button("💾 Save Settings"):
                # Save settings using the config service
                save_settings(whisper_model, ollama_model)
                
                # Update session state for immediate UI feedback
                st.session_state.whisper_model = whisper_model
                st.session_state.ollama_model = ollama_model
                
                # Show success toast/message
                st.success("Settings saved! Next audio file will use these models.")
                
                # Trigger rerun to update dashboard metrics and UI session states
                st.rerun()
        
        # Get current status from transcription service
        status = transcription_service.get_status()
        
        # Display processing metrics
        st.markdown("### Processing Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(label="Total Files Received", value=str(status["total_processed"]))
            
        with col2:
            st.metric(label="Processing Status", value=status["current_status"])
            
        with col3:
            st.metric(label="Pending Files", value=str(status["pending_files_count"]))
        
        # Display log table
        st.markdown("### Processing Log")
        
        # Get list of processed files from raw-markdown directory
        try:
            markdown_files = []
            if os.path.exists(RAW_MARKDOWN_DIR):
                for filename in os.listdir(RAW_MARKDOWN_DIR):
                    if filename.endswith('.md'):
                        filepath = os.path.join(RAW_MARKDOWN_DIR, filename)
                        stat = os.stat(filepath)
                        created_time = datetime.fromtimestamp(stat.st_ctime)
                        markdown_files.append({
                            'filename': filename,
                            'processed_date': created_time.strftime('%Y-%m-%d %H:%M'),
                            'status': 'Success'
                        })
            
            # Sort by date (newest first)
            markdown_files.sort(key=lambda x: x['processed_date'], reverse=True)
            
            if markdown_files:
                # Create a DataFrame for the table
                df = st.dataframe(markdown_files, use_container_width=True)
                
                # Add file selection for preview
                selected_file = st.selectbox("Select a file to preview:", 
                                           [f['filename'] for f in markdown_files] + [''])
                
                if selected_file:
                    # Show the content in an expandable code box
                    with st.expander(f"Preview: {selected_file}"):
                        try:
                            filepath = os.path.join(RAW_MARKDOWN_DIR, selected_file)
                            with open(filepath, 'r') as f:
                                content = f.read()
                            st.code(content, language='markdown')
                        except Exception as e:
                            st.error(f"Error reading file: {str(e)}")
            else:
                st.info("No processed files found yet.")
                
        except Exception as e:
            st.error(f"Error retrieving log data: {str(e)}")
    
    with tab2:
        st.subheader("System Analytics")
        st.info("System analytics and additional dashboard features coming soon!")