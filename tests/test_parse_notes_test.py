import os
import yaml
import json

# Define paths specific to your Obsidian folder
PROJECT_ROOT = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising"
CHAPTERS_DIR = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising\\Chapters"
OUTPUT_FILE = os.path.join(PROJECT_ROOT, "chapters.json")

# Function to parse YAML front matter from Markdown files
def parse_markdown(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        content = f.read()
        parts = content.split("---")
        
        if len(parts) > 2:
            metadata = yaml.safe_load(parts[1])
            body = "".join(parts[2:]).strip()
            return {"metadata": metadata, "body": body}
        else:
            return {"metadata": {}, "body": content.strip()}

# Main function to parse all chapters
def parse_chapters(directory):
    if not os.path.exists(directory):
        raise FileNotFoundError(f"The directory {directory} does not exist. Check the path.")
    
    print(f"Looking for Markdown files in: {directory}")
    chapters = []
    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            file_path = os.path.join(directory, filename)
            parsed_data = parse_markdown(file_path)
            chapters.append({"filename": filename, **parsed_data})
    return chapters

# Save parsed data as JSON
def save_to_json(data, output_file):
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4)

if __name__ == "__main__":
    # Parse all Markdown files in the Chapters directory
    parsed_chapters = parse_chapters(CHAPTERS_DIR)
    
    # Save the parsed data to chapters.json
    save_to_json(parsed_chapters, OUTPUT_FILE)
    print(f"Chapters parsed and saved to {OUTPUT_FILE}")
