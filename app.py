import streamlit as st
from components.sidebar import render_sidebar
from services.transcription_service import init_transcription_service
from services.config_service import load_settings, save_settings, get_available_ollama_models
from services.organization_service import (
    create_organized_folder,
    delete_organized_file,
    delete_organized_folder,
    list_available_prompts,
    list_organized_files,
    list_organized_folders,
    process_raw_markdown,
)
from services.processing_log_service import list_processing_logs
import os
from datetime import datetime

# Set page configuration
st.set_page_config(
    page_title="The Outlander Journaler",
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
    page_title="The Outlander Journaler",
    page_icon="🎤",
    layout="wide"
)

st.markdown(
    """
    <style>
    section[data-testid="stSidebar"] div[data-testid="stElementContainer"]:has(> div[data-testid="stButton"]) {
        width: 100% !important;
    }

    div[data-testid="stButton"] {
        width: 100% !important;
    }

    div[data-testid="stButton"] > button {
        width: 100% !important;
        min-height: 2.75rem !important;
        border: 2px solid color-mix(in srgb, currentColor 55%, transparent) !important;
        border-radius: 0.65rem !important;
        transition: background-color 140ms ease, box-shadow 140ms ease,
                    border-color 140ms ease, transform 140ms ease;
    }

    section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
        justify-content: flex-start;
        padding-inline: 1rem !important;
        text-align: left;
    }

    div[data-testid="stButton"] > button:not(:disabled):hover {
        border-color: currentColor !important;
        box-shadow: 0 0 0 3px color-mix(in srgb, currentColor 20%, transparent) !important;
        transform: translateY(-1px);
    }

    div[data-testid="stButton"] > button:not([kind="primary"]):not(:disabled):hover {
        background-color: color-mix(in srgb, currentColor 8%, transparent) !important;
    }

    div[data-testid="stButton"] > button:focus-visible {
        outline: 3px solid currentColor;
        outline-offset: 2px;
    }

    @media (prefers-reduced-motion: reduce) {
        div[data-testid="stButton"] > button {
            transition: none;
        }

        div[data-testid="stButton"] > button:not(:disabled):hover {
            transform: none;
        }
    }
    </style>
    """,
    unsafe_allow_html=True,
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

def is_valid_view(view):
    if view in {"Home", "Dashboard", "Logs"}:
        return True
    if view.startswith("Category_"):
        category = view.removeprefix("Category_")
        return category in {
            folder.replace("/", "_").replace("\\", "_")
            for folder in list_organized_folders()
        }
    return False


# Keep the current page in the URL so a browser refresh restores it.
requested_view = st.query_params.get("view", "Home")
if not is_valid_view(requested_view):
    requested_view = "Home"

if "current_view" not in st.session_state or not is_valid_view(st.session_state.current_view):
    st.session_state.current_view = requested_view

# Render sidebar
home_selected, dashboard_selected, category_selected, logs_selected = render_sidebar()

# Update view based on sidebar selection
if home_selected:
    st.session_state.current_view = "Home"
elif dashboard_selected:
    st.session_state.current_view = "Dashboard"
elif logs_selected:
    st.session_state.current_view = "Logs"
elif category_selected:
    # Sanitize the category name for use in session state
    sanitized_category = category_selected.replace("/", "_").replace("\\", "_")
    st.session_state.current_view = f"Category_{sanitized_category}"

if st.query_params.get("view") != st.session_state.current_view:
    st.query_params["view"] = st.session_state.current_view

# Main content area
st.title("The Outlander Journaler")

# Display current view
if st.session_state.current_view == "Home":
    # Home View
    st.markdown("""
    This application is a voice-to-markdown processing hub and content dashboard.
    
    You can use it to:
    - Convert voice recordings to markdown format
    - Manage your journal entries
    - View system statistics and analytics
    """)
    
elif st.session_state.current_view == "Dashboard":
    # Dashboard View
    st.header("Dashboard")
    processing_success_message = st.session_state.pop("processing_success_message", None)
    if processing_success_message:
        st.success(processing_success_message)
    dashboard_notice = st.session_state.pop("dashboard_notice", None)
    if dashboard_notice:
        st.success(dashboard_notice)
    
    with st.container():
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
        
        # Keep the dashboard status metrics together in one compact card.
        with st.container(border=True):
            st.markdown("**Processing Metrics**")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(label="Total Files Received", value=str(status["total_processed"]))

            with col2:
                st.metric(label="Processing Status", value=status["current_status"])

            with col3:
                st.metric(label="Pending Files", value=str(status["pending_files_count"]))
        
        # Display files waiting for processing
        with st.container(border=True):
            st.markdown("**Raw Markdown Queue**")
        
            # Get list of raw files awaiting processing.
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
                                'status': 'Pending'
                            })
                
                # Sort by date (newest first)
                markdown_files.sort(key=lambda x: x['processed_date'], reverse=True)
                
                if markdown_files:
                    st.dataframe(
                        markdown_files,
                        width='stretch',
                        height=160,
                        hide_index=True
                    )
                else:
                    st.info("No raw markdown files are pending processing.")

            except Exception as e:
                st.error(f"Error retrieving raw Markdown queue: {str(e)}")
    
        # Get list of markdown files from raw-markdown directory.
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
                st.info("No raw markdown files are waiting for processing.")
            else:
                st.markdown("### Raw Markdown Files")

                available_prompts = list_available_prompts()
                organized_folders = list_organized_folders()
                all_folders = organized_folders + ["+ Create New Folder"]

                for i, file_info in enumerate(markdown_files):
                    filename = file_info['filename']

                    with st.container(border=True):
                        col1, col2, col3, col4 = st.columns(
                            [2.2, 1.4, 1.4, 1],
                            vertical_alignment="bottom"
                        )

                        with col1:
                            st.markdown(f"**{filename}**")
                            st.caption(file_info['processed_date'])

                        with col2:
                            selected_folder = st.selectbox(
                                "Target Folder",
                                all_folders,
                                key=f"folder_{i}"
                            )

                        with col3:
                            selected_prompt = st.selectbox(
                                "Prompt Template",
                                available_prompts,
                                key=f"prompt_{i}"
                            )

                        with col4:
                            execute = st.button(
                                "Process",
                                key=f"execute_{i}",
                                type="primary",
                                width="stretch"
                            )

                        new_folder_name = ""
                        if selected_folder == "+ Create New Folder":
                            new_folder_name = st.text_input(
                                "New folder name",
                                key=f"new_folder_{i}"
                            )

                        if execute:
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
                            selected_model = st.session_state.get('ollama_model')
                            try:
                                processing_succeeded = process_raw_markdown(
                                    filename,
                                    selected_model,
                                    selected_prompt,
                                    target_folder,
                                )
                            except Exception as e:
                                st.error(f"Could not complete and log processing for {filename}: {e}")
                            else:
                                if processing_succeeded:
                                    st.session_state.processing_success_message = (
                                        f"Successfully processed and removed {filename} from the raw queue."
                                    )
                                    st.rerun()
                                else:
                                    st.error(f"Could not process {filename}. See Logs for details.")
                                    
        except Exception as e:
            st.error(f"Error retrieving raw Markdown files: {str(e)}")

    st.subheader("Manage Organized Content")
    st.caption("Permanently delete organized files or folders. Deleting a folder removes all its contents.")
    try:
        organized_files = list_organized_files()
        organized_folders = list_organized_folders()

        file_column, folder_column = st.columns(2)
        with file_column:
            selected_file = st.selectbox(
                "Organized file",
                options=organized_files,
                index=None,
                placeholder="Choose a file to delete",
                key="delete_organized_file_selection",
            )
            if selected_file:
                confirmed_file = st.checkbox(
                    f"Confirm permanent deletion of {selected_file}",
                    key=f"confirm_delete_file_{selected_file}",
                )
                if st.button(
                    "Delete file",
                    key="delete_organized_file_button",
                    disabled=not confirmed_file,
                    type="secondary",
                ):
                    delete_organized_file(selected_file)
                    st.session_state.dashboard_notice = f"Deleted {selected_file}."
                    st.rerun()

        with folder_column:
            selected_folder_to_delete = st.selectbox(
                "Organized folder",
                options=organized_folders,
                index=None,
                placeholder="Choose a folder to delete",
                key="delete_organized_folder_selection",
            )
            if selected_folder_to_delete:
                confirmed_folder = st.checkbox(
                    f"Confirm deletion of {selected_folder_to_delete} and all its contents",
                    key=f"confirm_delete_folder_{selected_folder_to_delete}",
                )
                if st.button(
                    "Delete folder and contents",
                    key="delete_organized_folder_button",
                    disabled=not confirmed_folder,
                    type="secondary",
                ):
                    delete_organized_folder(selected_folder_to_delete)
                    st.session_state.dashboard_notice = (
                        f"Deleted {selected_folder_to_delete} and its contents."
                    )
                    st.rerun()
    except Exception as e:
        st.error(f"Unable to manage organized content: {e}")

elif st.session_state.current_view == "Logs":
    st.header("Processing Logs")
    try:
        processing_logs = list_processing_logs()
        if processing_logs:
            for entry in processing_logs:
                entry["source_removed"] = "Yes" if entry["source_removed"] else "No"
            st.dataframe(
                processing_logs,
                width="stretch",
                hide_index=True,
            )
        else:
            st.info("No processing history yet.")
    except Exception as e:
        st.error(f"Unable to retrieve processing logs: {e}")

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