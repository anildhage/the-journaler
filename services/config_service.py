import json
import os
from pathlib import Path
import streamlit as st

# Configuration file path
CONFIG_FILE = "./config/settings.json"

# Default configuration values
DEFAULT_CONFIG = {
    "whisper_model": "base",
    "ollama_model": "llama3:latest"
}

# Available models
AVAILABLE_WHISPER_MODELS = ["tiny", "base", "small", "medium", "large"]
AVAILABLE_OLLAMA_MODELS = ["llama3:latest", "qwen2.5-coder:7b-instruct-q4_K_M", "Mistral:7b"]

def load_settings():
    """Load settings from settings.json. If missing, create it with defaults."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                loaded_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                final_config = DEFAULT_CONFIG.copy()
                final_config.update(loaded_config)
                return final_config
        else:
            # Create config file with defaults if it doesn't exist
            save_settings(DEFAULT_CONFIG["whisper_model"], DEFAULT_CONFIG["ollama_model"])
            return DEFAULT_CONFIG
    except Exception as e:
        print(f"Error loading config: {e}")
        return DEFAULT_CONFIG

def save_settings(whisper_model, ollama_model):
    """Write new choices to settings.json and update Streamlit session state."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(CONFIG_FILE), exist_ok=True)
        
        # Prepare configuration
        config = {
            "whisper_model": whisper_model,
            "ollama_model": ollama_model
        }
        
        with open(CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
        
        # Update Streamlit session state
        st.session_state.whisper_model = whisper_model
        st.session_state.ollama_model = ollama_model
        
    except Exception as e:
        print(f"Error saving config: {e}")

# Load initial settings
settings = load_settings()