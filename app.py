import streamlit as st
from components.sidebar import render_sidebar
from services.transcription_service import init_transcription_service
from services.config_service import load_settings, save_settings, get_available_ollama_models
from services.organization_service import list_available_prompts, list_organized_folders, create_organized_folder, process_raw_markdown
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
home_selected, dashboard_selected, category_selected = render_sidebar()

# Update view based on sidebar selection
if home_selected:
    st.session_state.current_view = "Home"
elif dashboard_selected:
    st.session_state.current_view = "Dashboard"
elif category_selected:
    # Sanitize the category name for use in session state
    sanitized_category = category_selected.replace("/", "_").replace("\\", "_")
    st.session_state.current_view = f"Category_{sanitized_category}"

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
    tab1, tab2, tab3 = st.tabs(["Audio Processing Status", "System Analytics", "Organise Raw Markdown"])
    
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
            try:
                whisper_model_index = ["tiny", "base", "small", "medium", "large"].index(current_whisper_model)
            except ValueError:
                # If the saved model is not in our list, default to the first option
                whisper_model_index = 0
            
            whisper_model = st.selectbox(
                "Whisper Model (STT)",
                options=["tiny", "base", "small", "medium", "large"],
                index=whisper_model_index,
                key="whisper_model_select"
            )
            
            # Ollama model selection - dynamically discover available models
            available_models = get_available_ollama_models()
            if not available_models:
                # If no models found, show a warning and use default fallback
                st.warning("No Ollama models found. Please pull at least one model in Ollama.")
                # Disable the selectbox since there are no valid options
                st.selectbox(
                    "Ollama Model (LLM)",
                    ["No models available - please pull models in Ollama"],
                    key="ollama_model_select",
                    disabled=True
                )
                ollama_model = None
            else:
                # Get the currently selected model from session state or use first available
                current_ollama_model = st.session_state.get('ollama_model', available_models[0])
                
                try:
                    ollama_model_index = available_models.index(current_ollama_model)
                except ValueError:
                    # If the saved model is not in our list, default to the first option
                    ollama_model_index = 0

                ollama_model = st.selectbox(
                    "Ollama Model (LLM)",
                    options=available_models,
                    index=ollama_model_index,
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
                df = st.dataframe(markdown_files, width='stretch')
                
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
        
    with tab3:
        st.subheader("Organise Raw Markdown")
        
        # Get list of markdown files from raw-markdown directory
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
                            'processed_date': created_time.strftime('%Y-%m-%d %H:%M')
                        })
            
            # Sort by date (newest first)
            markdown_files.sort(key=lambda x: x['processed_date'], reverse=True)
            
            if not markdown_files:
                st.info("No raw markdown files found in the inbox. Process some audio files first.")
            else:
                st.markdown("### Raw Markdown Files")
                
                # Create a table for each file
                for i, file_info in enumerate(markdown_files):
                    filename = file_info['filename']
                    
                    with st.expander(f"File: {filename}"):
                        # Get available prompts and organized folders
                        available_prompts = list_available_prompts()
                        organized_folders = list_organized_folders()
                        
                        # Add option to create new folder
                        all_folders = organized_folders + ["+ Create New Folder"]
                        
                        # Row for file controls
                        col1, col2, col3, col4, col5 = st.columns(5)
                        
                        with col1:
                            st.write(f"**File:** {filename}")
                            
                        with col2:
                            # Ollama model selection - dynamically discover available models
                            available_models = get_available_ollama_models()
                            if not available_models:
                                # If no models found, show a warning and use default fallback
                                st.warning("No Ollama models found. Please pull at least one model in Ollama.")
                                # Disable the selectbox since there are no valid options
                                st.selectbox(
                                    "Ollama Model",
                                    ["No models available - please pull models in Ollama"],
                                    key=f"model_{i}",
                                    disabled=True
                                )
                                selected_model = None
                            else:
                                # Get the currently selected model from session state or use first available
                                current_ollama_model = st.session_state.get('ollama_model', available_models[0])
                                
                                try:
                                    model_index = available_models.index(current_ollama_model)
                                except ValueError:
                                    # If the saved model is not in our list, default to the first option
                                    model_index = 0

                                selected_model = st.selectbox(
                                    "Ollama Model",
                                    available_models,
                                    index=model_index,
                                    key=f"model_{i}"
                                )
                            
                        with col3:
                            # Folder selection
                            selected_folder = st.selectbox(
                                "Target Folder",
                                all_folders,
                                key=f"folder_{i}"
                            )
                            
                            # Handle creating new folder
                            if selected_folder == "+ Create New Folder":
                                new_folder_name = st.text_input("New folder name:", key=f"new_folder_{i}")
                                
                        with col4:
                            # Prompt template selection
                            selected_prompt = st.selectbox(
                                "Prompt Template",
                                available_prompts,
                                key=f"prompt_{i}"
                            )
                            
                        with col5:
                            # Execute button
                            if st.button("🚀 Execute LLM", key=f"execute_{i}"):
                                # If creating new folder, create it first
                                target_folder = selected_folder
                                if selected_folder == "+ Create New Folder" and new_folder_name.strip():
                                    if create_organized_folder(new_folder_name):
                                        target_folder = new_folder_name
                                        st.success(f"Created new folder: {new_folder_name}")
                                    else:
                                        st.error(f"Failed to create folder: {new_folder_name}")
                                        continue
                                elif selected_folder == "+ Create New Folder":
                                    st.error("Please enter a name for the new folder")
                                    continue
                                
                                # Execute the processing
                                if process_raw_markdown(filename, selected_model, selected_prompt, target_folder):
                                    st.success(f"Successfully processed {filename}!")
                                else:
                                    st.error(f"Failed to process {filename}")
                                    
        except Exception as e:
            st.error(f"Error retrieving files: {str(e)}")

else:
    # Handle category view
    if st.session_state.current_view.startswith("Category_"):
        # Extract category name, handling potential sanitization issues
        category_name = st.session_state.current_view.replace("Category_", "", 1)
        
        st.header(f"📁 {category_name}")
        
        # Get the organized directory for this category
        category_dir = f"./organized/{category_name}"
        
        if os.path.exists(category_dir):
            try:
                # Get all markdown files in this category
                markdown_files = []
                for filename in os.listdir(category_dir):
                    if filename.endswith('.md'):
                        filepath = os.path.join(category_dir, filename)
                        stat = os.stat(filepath)
                        created_time = datetime.fromtimestamp(stat.st_ctime)
                        markdown_files.append({
                            'filename': filename,
                            'created_date': created_time.strftime('%Y-%m-%d %H:%M'),
                            'filepath': filepath
                        })
                
                # Sort by date (newest first)
                markdown_files.sort(key=lambda x: x['created_date'], reverse=True)
                
                if not markdown_files:
                    st.info(f"No markdown files found in {category_name} category.")
                else:
                    # Display each file as a card
                    for file_info in markdown_files:
                        filename = file_info['filename']
                        filepath = file_info['filepath']
                        
                        with st.expander(f"📄 {filename}"):
                            try:
                                with open(filepath, 'r') as f:
                                    content = f.read()
                                
                                # Display the formatted markdown content
                                st.markdown(content)
                                
                            except Exception as e:
                                st.error(f"Error reading file: {str(e)}")
                                
            except Exception as e:
                st.error(f"Error retrieving files from {category_name}: {str(e)}")
        else:
            st.error(f"Category directory not found: {category_dir}")