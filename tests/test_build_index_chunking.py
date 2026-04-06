import os
import json
import re
import nltk
from nltk.tokenize import sent_tokenize

# Constants for chunking
CHUNK_SIZE = 300

# File paths
CHARACTERS_FOLDER = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising\\Characters"
CHAPTERS_FILE = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising\\chapters.json"
OUTPUT_FILE = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising\\all_data_chunked.json"

def chunk_text(text, max_chunk_size):
    sentences = sent_tokenize(text)
    chunks, current_chunk = [], []
    current_length = 0
    for sentence in sentences:
        sentence_length = len(sentence.split())
        if current_length + sentence_length > max_chunk_size:
            chunks.append(' '.join(current_chunk))
            current_chunk = []
            current_length = 0
        current_chunk.append(sentence)
        current_length += sentence_length
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    return chunks

def extract_tags_from_markdown(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        match = re.search(r"---(.*?)---", content, re.DOTALL)
        if match:
            front_matter = match.group(1)
            tags_match = re.search(r"tags:\s*(\[[^\]]*\]|\S+)", front_matter)
            if tags_match:
                tags_raw = tags_match.group(1)
                if tags_raw.startswith("[") and tags_raw.endswith("]"):
                    return [tag.strip().strip("'\"") for tag in tags_raw[1:-1].split(",")]
                else:
                    return [tag.strip() for tag in tags_raw.split(",")]
        return []
    except Exception as e:
        print(f"Error extracting tags from {filepath}: {e}")
        return []

def process_characters_and_chapters(characters_folder, chapters_file, output_file, chunk_size):
    if not os.path.exists(characters_folder):
        print(f"Error: Characters folder not found at {characters_folder}")
        return
    if not os.path.exists(chapters_file):
        print(f"Error: Chapters file not found at {chapters_file}")
        return

    data = []
    for filename in os.listdir(characters_folder):
        if filename.endswith(".md"):
            filepath = os.path.join(characters_folder, filename)
            print(f"Processing character file: {filepath}")
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    text = f.read()
                tags = extract_tags_from_markdown(filepath)
                chunks = chunk_text(text, chunk_size)
                data.append({
                    "type": "character",
                    "filename": filename,
                    "tags": tags,
                    "chunks": chunks
                })
            except Exception as e:
                print(f"Error processing character file {filename}: {e}")

    print(f"Processing chapters file: {chapters_file}")
    try:
        with open(chapters_file, "r", encoding="utf-8") as f:
            chapters = json.load(f)
            for chapter in chapters:
                body = chapter.get("body", "")
                chunks = chunk_text(body, chunk_size)
                data.append({
                    "type": "chapter",
                    "filename": chapter.get("filename"),
                    "metadata": chapter.get("metadata", {}),
                    "tags": chapter.get("tags", []),
                    "chunks": chunks
                })
    except Exception as e:
        print(f"Error processing chapters file: {e}")

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"Combined chunked data saved to {output_file}")
    except Exception as e:
        print(f"Error saving chunked data: {e}")

if __name__ == "__main__":
    nltk.download('punkt_tab')
    process_characters_and_chapters(CHARACTERS_FOLDER, CHAPTERS_FILE, OUTPUT_FILE, CHUNK_SIZE)


