"""
Organization Service Module

This module handles the processing of raw Markdown files using Ollama models
with custom prompt templates, and saves the organized output to destination folders.
"""

import os
import json
import shutil
from pathlib import Path
from typing import List
import ollama

# Import configuration constants
from project_config import RAW_MARKDOWN_DIR, PROMPTS_DIR, ORGANIZED_ROOT_DIR
from services.config_service import get_available_ollama_models
from services.processing_log_service import (
    record_processing_attempt,
    update_processing_attempt,
)


def transform_and_organize_markdown(raw_filename, selected_model, selected_prompt_file, target_folder):
    """
    Process a raw Markdown file using Ollama with a custom prompt and save to destination folder.
    
    Args:
        raw_filename (str): Name of the raw markdown file to process
        selected_model (str): Ollama model to use for processing
        selected_prompt_file (str): Name of the prompt template file to use
        target_folder (str): Destination folder name within ./organized/
        
    Returns:
        tuple: (success: bool, message: str)
    """
    
    try:
        # Validate that the Ollama model is available
        available_models = get_available_ollama_models()
        if selected_model not in available_models:
            return False, f"Selected model '{selected_model}' is not available. Available models: {available_models}"
        
        # Define directory paths
        raw_markdown_dir = "./raw-markdown"
        prompts_dir = "./prompts"
        organized_root_dir = "./organized"
        
        # Construct full file paths
        raw_file_path = os.path.join(raw_markdown_dir, raw_filename)
        prompt_file_path = os.path.join(prompts_dir, selected_prompt_file)
        target_folder_path = os.path.join(organized_root_dir, target_folder)
        output_file_path = os.path.join(target_folder_path, raw_filename)
        
        # Verify source files exist
        if not os.path.exists(raw_file_path):
            return False, f"Raw markdown file not found: {raw_file_path}"
            
        if not os.path.exists(prompt_file_path):
            return False, f"Prompt template file not found: {prompt_file_path}"
        
        # Create target folder if it doesn't exist
        os.makedirs(target_folder_path, exist_ok=True)
        
        # Read raw markdown content
        with open(raw_file_path, 'r', encoding='utf-8') as f:
            raw_content = f.read()
            
        # Read prompt template
        with open(prompt_file_path, 'r', encoding='utf-8') as f:
            prompt_template = f.read()
        
        # Prepare the prompt by combining template with raw content
        full_prompt = f"{prompt_template}\n\n---\n\n{raw_content}"
        
        # Send to Ollama for processing
        response = ollama.chat(
            model=selected_model,
            messages=[
                {
                    'role': 'user',
                    'content': full_prompt
                }
            ]
        )
        
        # Extract the response content
        organized_content = response['message']['content']
        
        # Write the organized content to output file
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(organized_content)
            
        return True, f"Successfully processed {raw_filename} and saved to {target_folder}/{raw_filename}"
        
    except ollama.ResponseError as e:
        error_msg = f"Ollama response error: {e.error}"
        return False, error_msg
        
    except Exception as e:
        error_msg = f"Error processing file: {str(e)}"
        return False, error_msg


def process_raw_markdown(raw_filename, selected_model, selected_prompt_file, target_folder):
    """
    Process a raw file, persist its result, and remove it after successful processing.
    
    Args:
        raw_filename (str): Name of the raw markdown file to process
        selected_model (str): Ollama model to use for processing
        selected_prompt_file (str): Name of the prompt template file to use
        target_folder (str): Destination folder name within ./organized/
        
    Returns:
        bool: True if successful, False otherwise
    """
    success, message = transform_and_organize_markdown(
        raw_filename,
        selected_model,
        selected_prompt_file,
        target_folder,
    )
    if not success:
        record_processing_attempt(
            raw_filename,
            "Failed",
            message,
            selected_model,
            selected_prompt_file,
            target_folder,
        )
        return False

    log_id = record_processing_attempt(
        raw_filename,
        "Processing succeeded",
        message,
        selected_model,
        selected_prompt_file,
        target_folder,
    )
    raw_file_path = os.path.join(RAW_MARKDOWN_DIR, raw_filename)
    try:
        os.remove(raw_file_path)
    except OSError as error:
        update_processing_attempt(
            log_id,
            "Cleanup failed",
            f"{message}. Could not remove raw file: {error}",
            False,
        )
        return False

    update_processing_attempt(log_id, "Success", message, True)
    return True


def list_available_prompts() -> List[str]:
    """
    Get a list of all available prompt template files.
    
    Returns:
        List[str]: List of prompt filenames
    """
    prompts_dir = "./prompts"
    if not os.path.exists(prompts_dir):
        return []
    
    try:
        prompt_files = [f for f in os.listdir(prompts_dir) if f.endswith('.md')]
        return sorted(prompt_files)
    except Exception:
        return []


def list_organized_folders() -> List[str]:
    """
    Get a list of all organized folders (subdirectories in ./organized/).
    
    Returns:
        List[str]: List of folder names
    """
    organized_dir = "./organized"
    if not os.path.exists(organized_dir):
        return []
    
    try:
        folders = [d for d in os.listdir(organized_dir) if os.path.isdir(os.path.join(organized_dir, d))]
        return sorted(folders)
    except Exception:
        return []


def create_organized_folder(folder_name: str) -> bool:
    """
    Create a new organized folder.
    
    Args:
        folder_name (str): Name of the folder to create
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        organized_dir = "./organized"
        folder_path = os.path.join(organized_dir, folder_name)
        os.makedirs(folder_path, exist_ok=True)
        return True
    except Exception:
        return False


def list_organized_files() -> List[str]:
    """List files under organized folders using paths relative to the root."""
    organized_root = Path(ORGANIZED_ROOT_DIR).resolve()
    if not organized_root.exists():
        return []

    files = []
    for path in organized_root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        relative_path = path.relative_to(organized_root)
        current = organized_root
        for part in relative_path.parts:
            current = current / part
            if current.is_symlink():
                break
        else:
            files.append(relative_path.as_posix())
    return sorted(files)


def _get_organized_path(relative_path: str) -> Path:
    """Resolve a path inside organized storage and reject traversal or symlinks."""
    relative = Path(relative_path)
    if relative.is_absolute() or not relative.parts or ".." in relative.parts:
        raise ValueError("Choose a valid path inside an organized folder.")

    organized_root = Path(ORGANIZED_ROOT_DIR).resolve()
    candidate = organized_root
    for part in relative.parts:
        candidate = candidate / part
        if candidate.is_symlink():
            raise ValueError("Organized content symlinks cannot be deleted from the app.")

    resolved = candidate.resolve()
    if resolved == organized_root or not resolved.is_relative_to(organized_root):
        raise ValueError("The selected path is outside organized storage.")
    return candidate


def delete_organized_file(relative_path: str) -> None:
    """Permanently delete one file from organized storage."""
    file_path = _get_organized_path(relative_path)
    if not file_path.is_file():
        raise FileNotFoundError(f"Organized file not found: {relative_path}")
    file_path.unlink()


def delete_organized_folder(folder_name: str) -> None:
    """Permanently delete a top-level organized folder and all its contents."""
    folder_path = _get_organized_path(folder_name)
    organized_root = Path(ORGANIZED_ROOT_DIR).resolve()
    if folder_path.parent != organized_root or not folder_path.is_dir():
        raise ValueError("Choose an existing top-level organized folder.")
    shutil.rmtree(folder_path)


# Test function for development
def test_organization_service():
    """Test function to verify the organization service works correctly."""
    
    # List available models for testing
    print("Available Ollama models:", get_available_ollama_models())
    
    # Try to process a sample file (this will fail if no files exist)
    try:
        success, message = transform_and_organize_markdown(
            raw_filename="sample.md",
            selected_model=None,  # Will be handled by the UI
            selected_prompt_file="default_blog.md",
            target_folder="test"
        )
        print(f"Test result: {success} - {message}")
    except Exception as e:
        print(f"Test error (expected if files don't exist): {e}")


if __name__ == "__main__":
    test_organization_service()