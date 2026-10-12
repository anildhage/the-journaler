import os

# Define directory paths
INBOX_DIR = "./inbox"
RAW_MARKDOWN_DIR = "./raw-markdown"
PROMPTS_DIR = "./prompts"
ORGANIZED_ROOT_DIR = "./organized"

# Create directories if they don't exist
os.makedirs(INBOX_DIR, exist_ok=True)
os.makedirs(RAW_MARKDOWN_DIR, exist_ok=True)
os.makedirs(PROMPTS_DIR, exist_ok=True)
os.makedirs(ORGANIZED_ROOT_DIR, exist_ok=True)

# Create default prompt template if prompts directory is empty
if not os.listdir(PROMPTS_DIR):
    default_prompt_content = """# Default Blog Prompt

You are a helpful assistant that helps convert voice notes into well-structured blog posts.

## Task
Convert the provided audio transcription into a professional blog post with:
1. An engaging introduction
2. Well-organized body sections
3. Clear conclusions
4. Proper formatting and structure

## Guidelines
- Maintain the original meaning and intent
- Use clear, concise language
- Structure content logically
- Add any relevant context or explanations where needed
- Keep paragraphs appropriately sized
- Use markdown formatting for headers, lists, and emphasis

## Output Format
Use markdown format for the blog post with:
- # for main headings
- ## for subheadings  
- Bullet points for lists
- Emphasis for important terms

## Input
{transcription}"""
    
    default_prompt_path = os.path.join(PROMPTS_DIR, "default_blog.md")
    with open(default_prompt_path, 'w') as f:
        f.write(default_prompt_content)