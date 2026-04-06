import json
import os
import faiss
import numpy as np
from openai import OpenAI
from test_build_index_chunking import process_chapters  # Import the chunking script

# Path to the JSON file and FAISS index
ORIGINAL_JSON_FILE_PATH = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising\\chapters.json"
CHUNKED_JSON_FILE_PATH = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising\\chapters_chunked.json"
INDEX_FILE_PATH = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising\\semantic_index.faiss"

# Instantiate the OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def build_index(json_file_path, index_file_path):
    # Load the chunked JSON file
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            chapters = json.load(f)
    except Exception as e:
        print(f"Error reading the JSON file: {e}")
        return

    # Initialize FAISS index
    dimension = 1536  # Dimension of OpenAI embeddings
    index = faiss.IndexFlatL2(dimension)

    metadata_list = []  # Store metadata for each chunk

    for chapter in chapters:
        filename = chapter.get("filename")
        metadata = chapter.get("metadata", {})
        chunks = chapter.get("chunks", [])  # Use pre-chunked text from the JSON

        for i, chunk in enumerate(chunks):
            try:
                # Generate embedding with OpenAI
                response = client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=[chunk]  # Note: input must be a list
                )
                embedding = np.array(response.data[0].embedding, dtype=np.float32)

                # Add embedding to FAISS index
                index.add(np.array([embedding]))

                # Store metadata
                metadata_list.append({
                    "filename": filename,
                    "chapter_id": metadata.get("chapter_id"),
                    "chunk_id": f"{filename}_chunk_{i}",
                    "tags": metadata.get("tags", []),
                    "text": chunk
                })

            except Exception as e:
                print(f"Error embedding chunk {i} of {filename}: {e}")

    # Save FAISS index
    faiss.write_index(index, index_file_path)
    print(f"FAISS index saved to {index_file_path}")

    # Save metadata as a JSON file
    metadata_file_path = os.path.splitext(index_file_path)[0] + "_metadata.json"
    try:
        with open(metadata_file_path, "w", encoding="utf-8") as f:
            json.dump(metadata_list, f, indent=4)
        print(f"Metadata saved to {metadata_file_path}")
    except Exception as e:
        print(f"Error saving metadata: {e}")

if __name__ == "__main__":
    # First, chunk the text using the new chunking script
    process_chapters(ORIGINAL_JSON_FILE_PATH, CHUNKED_JSON_FILE_PATH, chunk_size=300)

    # Then, build the FAISS index using the chunked JSON
    build_index(CHUNKED_JSON_FILE_PATH, INDEX_FILE_PATH)

