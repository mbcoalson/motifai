import os
from openai import OpenAI
import yaml
from dotenv import load_dotenv
from WaterRisingProject.tests.test_openai_cost_calculator import OpenAICostCalculator

# Initialize OpenAI client and cost calculator
cost_calculator = OpenAICostCalculator()

# Load environment variables from .env file
load_dotenv()

# Constants
CHAPTERS_DIR = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising\\Chapters"

# Initialize OpenAI client
client = OpenAI(
    api_key=os.getenv("OPENAI_API_KEY")  # Load API key from environment
)

# Ensure API key is loaded
if not client.api_key:
    raise ValueError("OpenAI API key is not set. Check your .env file.")

def call_openai_api(prompt, model="gpt-4o"):
    """Call OpenAI API with the provided prompt and return the response content."""
    try:
        response = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=model,
            temperature=0.5
        )
        # Access the content correctly using attributes instead of subscripting
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

def parse_yaml_front_matter(content):
    """Parse YAML front matter and split the body from the Markdown content."""
    parts = content.split("---")
    if len(parts) < 3:
        return None, None
    metadata = yaml.safe_load(parts[1]) or {}
    body = "".join(parts[2:]).strip()
    return metadata, body

def update_yaml_front_matter(metadata, body):
    """Reconstruct the file content with updated YAML metadata."""
    return f"---\n{yaml.dump(metadata, default_flow_style=False)}---\n{body}"

def generate_metadata(content, filename=None):
    """Generate metadata using OpenAI."""
    prompt = f"""
    You are an expert in analyzing story content for themes, characters, and narrative elements. 
    Read the following text and generate metadata for the following fields: 
    - Title (default to the filename if not derivable)
    - Tags (3-5 keywords summarizing the text)
    - Characters (list of major characters)
    - Themes (list of 2-3 overarching themes)
    - Tone (description of the tone, e.g., dark, hopeful, tense)
    - Summary (brief summary of the chapter content)
    
    Text: "{content}"
    
    Provide the output as a JSON object with the keys: title, tags, characters, themes, tone, summary.
    """
    response = call_openai_api(prompt)
    if response:
        try:
            metadata = yaml.safe_load(response)
            if filename and not metadata.get("title"):
                metadata["title"] = filename
            return metadata
        except Exception as e:
            print(f"Error parsing metadata: {e}")
    return {}

def process_chapter_file(file_path):
    """Process a single chapter file, updating its metadata."""
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()

    metadata, body = parse_yaml_front_matter(content)
    if metadata is None:
        print(f"Skipping {file_path}: No valid YAML front matter.")
        return

    # Generate missing metadata
    filename = os.path.basename(file_path).replace(".md", "")
    print(f"Generating metadata for {filename}...")
    new_metadata = generate_metadata(body, filename)

    # Merge with existing metadata
    for key, value in new_metadata.items():
        if key not in metadata or not metadata[key]:
            metadata[key] = value

    # Write updated content back to file
    updated_content = update_yaml_front_matter(metadata, body)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(updated_content)

    print(f"Updated {filename} with metadata: {metadata}")

def apply_metadata_to_chapters(directory):
    """Apply metadata updates to all chapters in the specified directory."""
    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            file_path = os.path.join(directory, filename)
            process_chapter_file(file_path)

# Apply metadata to all chapters
apply_metadata_to_chapters(CHAPTERS_DIR)
