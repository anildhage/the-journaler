import os

# Define directory paths
INBOX_DIR = "./inbox"
RAW_MARKDOWN_DIR = "./raw-markdown"

# Create directories if they don't exist
os.makedirs(INBOX_DIR, exist_ok=True)
os.makedirs(RAW_MARKDOWN_DIR, exist_ok=True)