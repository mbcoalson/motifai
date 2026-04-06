import os
import yaml

# Paths
CHAPTERS_DIR = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising\\Chapters"

# New template structure
NEW_TEMPLATE = {
    "title": None,  # Will dynamically derive from filename if not set
    "tags": [],
    "date": None,
    "characters": [],
    "themes": [],
    "tone": "",
    "summary": "",
}

def apply_template_to_chapters(directory, template):
    for filename in os.listdir(directory):
        if filename.endswith(".md"):
            file_path = os.path.join(directory, filename)
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Split into YAML metadata and body
            parts = content.split("---")
            if len(parts) < 3:
                print(f"Skipping {filename}: No valid YAML front matter.")
                continue

            # Parse existing metadata
            existing_metadata = yaml.safe_load(parts[1])
            body = "".join(parts[2:]).strip()

            # Merge with the new template
            updated_metadata = template.copy()
            updated_metadata.update(existing_metadata or {})

            # Dynamically derive the title if not present
            if not updated_metadata.get("title"):
                updated_metadata["title"] = filename.replace(".md", "")

            # Reconstruct the file with updated metadata
            updated_content = f"---\n{yaml.dump(updated_metadata, default_flow_style=False)}---\n{body}"
            
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(updated_content)

            print(f"Updated {filename} with title: {updated_metadata['title']}")

# Apply the template to all chapters
apply_template_to_chapters(CHAPTERS_DIR, NEW_TEMPLATE)
