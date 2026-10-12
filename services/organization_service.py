import os
import json
from pathlib import Path
from typing import List
import ollama

# Import configuration constants
from project_config import RAW_MARKDOWN_DIR, PROMPTS_DIR, ORGANIZED_ROOT_DIR

def list_available_prompts() -> List[str]:
    """Returns a list of prompt filenames from ./prompts/ directory."""
    if not os.path.exists(PROMPTS_DIR):
        return []
    
    try:
        # Get all .md files in prompts directory
        prompts = [f for f in os.listdir(PROMPTS_DIR) if f.endswith('.md')]
        return sorted(prompts)
    except Exception as e:
        print(f"Error listing prompts: {e}")
        return []

def list_organized_folders() -> List[str]:
    """Returns all existing subfolders inside ./organized/ directory."""
    if not os.path.exists(ORGANIZED_ROOT_DIR):
        return []
    
    try:
        # Get all directories in organized root
        folders = [d for d in os.listdir(ORGANIZED_ROOT_DIR) 
                  if os.path.isdir(os.path.join(ORGANIZED_ROOT_DIR, d))]
        return sorted(folders)
    except Exception as e:
        print(f"Error listing organized folders: {e}")
        return []

def create_organized_folder(folder_name: str) -> bool:
    """Creates a new subfolder inside ./organized/<folder_name>."""
    try:
        folder_path = os.path.join(ORGANIZED_ROOT_DIR, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating organized folder: {e}")
        return False

def process_raw_markdown(raw_filename: str, selected_model: str, selected_prompt_file: str, target_folder: str) -> bool:
    """
    Process a raw Markdown file through Ollama using the selected prompt.
    
    Args:
        raw_filename (str): Name of the raw markdown file to process
        selected_model (str): Ollama model to use for processing
        selected_prompt_file (str): Name of the prompt template file to use
        target_folder (str): Target folder in organized directory for output
    
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # Validate inputs
        if not raw_filename or not selected_model or not selected_prompt_file or not target_folder:
            print("Error: All parameters must be provided")
            return False
        
        # Construct file paths
        raw_file_path = os.path.join(RAW_MARKDOWN_DIR, raw_filename)
        prompt_file_path = os.path.join(PROMPTS_DIR, selected_prompt_file)
        output_folder_path = os.path.join(ORGANIZED_ROOT_DIR, target_folder)
        
        # Ensure output folder exists
        os.makedirs(output_folder_path, exist_ok=True)
        
        # Read raw markdown content
        if not os.path.exists(raw_file_path):
            print(f"Error: Raw file {raw_filename} not found")
            return False
        
        with open(raw_file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
        
        # Read prompt template
        if not os.path.exists(prompt_file_path):
            print(f"Error: Prompt file {selected_prompt_file} not found")
            return False
        
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        # Construct the LLM payload by combining prompt instructions + raw markdown content
        llm_payload = prompt_template.format(transcription=raw_content)
        
        # Execute ollama.chat() locally
        response = ollama.chat(
            model=selected_model,
            messages=[
                {
                    'role': 'user',
                    'content': llm_payload
                }
            ]
        )
        
        # Extract the generated content
        transformed_content = response['message']['content']
        
        # Save the resulting transformed Markdown file
        output_file_path = os.path.join(output_folder_path, raw_filename)
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(transformed_content)
        
        print(f"Successfully processed {raw_filename} using model {selected_model}")
        return True
        
    except Exception as e:
        print(f"Error processing markdown file: {e}")
        return False