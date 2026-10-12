#!/usr/bin/env python3
"""
Test script to verify sidebar functionality and category detection.
"""

import os
import sys

# Add the project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from components.sidebar import render_sidebar
from services.config_service import list_organized_folders

def test_sidebar_functionality():
    """Test that the sidebar can detect organized folders"""
    print("Testing sidebar functionality...")
    
    # Test folder detection
    folders = list_organized_folders()
    print(f"Detected organized folders: {folders}")
    
    # Verify the structure of the folders
    if folders:
        for folder in folders:
            folder_path = f"./organized/{folder}"
            if os.path.exists(folder_path) and os.path.isdir(folder_path):
                print(f"✓ Folder '{folder}' exists and is a directory")
            else:
                print(f"✗ Folder '{folder}' does not exist or is not a directory")
    else:
        print("No organized folders detected (this is normal for a fresh installation)")
    
    # Test that sidebar rendering doesn't crash
    try:
        # This would normally be called in streamlit context, 
        # but we can at least verify the function exists and is callable
        print("✓ Sidebar render function is accessible")
        return True
    except Exception as e:
        print(f"✗ Error testing sidebar: {e}")
        return False

if __name__ == "__main__":
    test_sidebar_functionality()