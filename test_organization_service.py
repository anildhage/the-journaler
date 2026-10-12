#!/usr/bin/env python3
"""Test script to verify organization service is working correctly."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.organization_service import transform_and_organize_markdown

def test_organization_service():
    print("Testing organization service...")
    
    # Test with a sample call - this will fail if no files exist but should show proper error handling
    success, message = transform_and_organize_markdown(
        raw_filename="sample.md",
        selected_model=None,  # Will be handled by the UI
        selected_prompt_file="default_blog.md",
        target_folder="test"
    )
    print(f"Test result: {success} - {message}")

if __name__ == "__main__":
    test_organization_service()