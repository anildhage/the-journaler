import json
import os
import ollama
from pathlib import Path
import streamlit as st

# Configuration file path
CONFIG_FILE = "./config/settings.json"

# Default configuration values
DEFAULT_CONFIG = {
    "whisper_model": "base",
    "ollama_model": "llama3:latest"
}

def get_available_ollama_models():
    """Dynamically discover available Ollama models using ollama.list()"""
    try:
        # Get the OLLAMA_HOST from environment variable with default fallback
        ollama_host = os.getenv("OLLAMA_HOST", "http://localhost:11434")
        
        # Create a client with the host setting
        # Note: ollama library will automatically use the OLLAMA_HOST env var
        response = ollama.list()
        
        # Extract model names from the response - handle different response structures
        model_names = []
        
        # The response is an ollama._types.ListResponse object with a 'models' attribute
        if hasattr(response, 'models'):
            models = response.models
            for model in models:
                try:
                    # For ollama response objects, the model name is in the 'model' attribute
                    if hasattr(model, 'model'):
                        model_names.append(model.model)
                    elif isinstance(model, dict) and 'name' in model:
                        model_names.append(model['name'])
                    elif isinstance(model, str):
                        # If it's already a string, use as-is
                        model_names.append(model)
                except Exception as e:
                    print(f"Warning: Could not extract name from model {model}: {e}")
                    continue
        else:
            # Fallback for different response formats
            models = response.get('models', [])
            for model in models:
                try:
                    if isinstance(model, dict) and 'name' in model:
                        model_names.append(model['name'])
                    elif isinstance(model, str):
                        model_names.append(model)
                except Exception as e:
                    print(f"Warning: Could not extract name from model {model}: {e}")
                    continue
        
        # If no models found, return empty list instead of hardcoded fallback
        return sorted(model_names)
    except Exception as e:
        print(f"Error discovering Ollama models: {e}")
        # Return empty list to indicate no models available, let UI handle the fallback
        return []

def list_available_prompts():
    """Returns a list of prompt filenames from ./prompts/ directory."""
    prompts_dir = "./prompts"
    if not os.path.exists(prompts_dir):
        return []
    
    try:
        # Get all .md files in prompts directory
        prompts = [f for f in os.listdir(prompts_dir) if f.endswith('.md')]
        return sorted(prompts)
    except Exception as e:
        print(f"Error listing prompts: {e}")
        return []

def list_organized_folders():
    """Returns all existing subfolders inside ./organized/ directory."""
    organized_root_dir = "./organized"
    if not os.path.exists(organized_root_dir):
        return []
    
    try:
        # Get all directories in organized root
        folders = [d for d in os.listdir(organized_root_dir) 
                  if os.path.isdir(os.path.join(organized_root_dir, d))]
        return sorted(folders)
    except Exception as e:
        print(f"Error listing organized folders: {e}")
        return []

def create_organized_folder(folder_name):
    """Creates a new subfolder inside ./organized/<folder_name>."""
    try:
        folder_path = os.path.join("./organized", folder_name)
        os.makedirs(folder_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating organized folder: {e}")
        return False

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