import json
import os
import faiss
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from test_build_index_chunking import process_characters_and_chapters

# Load environment variables from .env file
load_dotenv()
print(f"Loaded API Key: {os.getenv('OPENAI_API_KEY')}")

# Instantiate OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Dynamically get project root regardless of where script is executed
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(PROJECT_ROOT, ".."))  # Go up one level

# Define input/output paths relative to project root
CHARACTERS_FOLDER = os.path.join(PROJECT_ROOT, "data", "raw", "Characters")
CHAPTERS_FILE = os.path.join(PROJECT_ROOT, "data", "raw", "chapters.json")
CHUNKED_JSON_FILE_PATH = os.path.join(PROJECT_ROOT, "data", "processed", "all_data_chunked.json")
INDEX_FILE_PATH = os.path.join(PROJECT_ROOT, "data", "faiss_index.pkl")
METADATA_FILE_PATH = os.path.join(PROJECT_ROOT, "data", "faiss_index_metadata.json")

def build_index(json_file_path, index_file_path):
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading the JSON file: {e}")
        return

    dimension = 1536
    index = faiss.IndexFlatL2(dimension)
    metadata_list = []

    for entry in data:
        filename = entry.get("filename")
        tags = entry.get("tags", [])
        metadata = entry.get("metadata", {})
        chunks = entry.get("chunks", [])

        for i, chunk in enumerate(chunks):
            try:
                response = client.embeddings.create(
                    model="text-embedding-ada-002",
                    input=[chunk]
                )
                embedding = np.array(response.data[0].embedding, dtype=np.float32)
                index.add(np.array([embedding]))

                metadata_list.append({
                    "filename": filename,
                    "chunk_id": f"{filename}_chunk_{i}",
                    "tags": tags,
                    "metadata": metadata,
                    "text": chunk
                })

            except Exception as e:
                print(f"Error embedding chunk {i} of {filename}: {e}")

    try:
        faiss.write_index(index, index_file_path)
        print(f"FAISS index saved to {index_file_path}")
    except Exception as e:
        print(f"Error saving FAISS index: {e}")

    try:
        with open(METADATA_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(metadata_list, f, indent=4)
        print(f"Metadata saved to {METADATA_FILE_PATH}")
    except Exception as e:
        print(f"Error saving metadata: {e}")


if __name__ == "__main__":
    try:
        print("Starting the chunking process...")
        process_characters_and_chapters(CHARACTERS_FOLDER, CHAPTERS_FILE, CHUNKED_JSON_FILE_PATH, chunk_size=300)
        print("Chunking process completed successfully!")

        print("Starting the FAISS index build process...")
        build_index(CHUNKED_JSON_FILE_PATH, INDEX_FILE_PATH)
        print("FAISS index built successfully!")
    except Exception as e:
        print(f"Error during the process: {e}")
