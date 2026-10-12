#!/usr/bin/env python3
"""
Simple test to verify the functionality of the organized folders detection.
"""

import os
import sys

def test_folder_detection():
    """Test that we can properly detect organized folders"""
    print("Testing organized folder detection...")
    
    # Test folder detection
    organized_dir = "./organized"
    
    if not os.path.exists(organized_dir):
        print(f"✓ Organized directory does not exist (this is expected): {organized_dir}")
        return True
    
    try:
        # Get all subdirectories in organized folder
        folders = []
        for item in os.listdir(organized_dir):
            item_path = os.path.join(organized_dir, item)
            if os.path.isdir(item_path):
                folders.append(item)
        
        print(f"Detected organized folders: {folders}")
        return True
        
    except Exception as e:
        print(f"✗ Error detecting organized folders: {e}")
        return False

if __name__ == "__main__":
    success = test_folder_detection()
    if success:
        print("✓ Folder detection test completed successfully")
    else:
        print("✗ Folder detection test failed")