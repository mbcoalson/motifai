import json
import os
import faiss
import numpy as np
from openai import OpenAI
from dotenv import load_dotenv
from test_build_index_chunking import process_characters_and_chapters  # Import the chunking script

# Path to the JSON files and FAISS index
CHARACTERS_FOLDER = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising\\Characters"
CHAPTERS_FILE = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising\\chapters.json"
CHUNKED_JSON_FILE_PATH = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising\\all_data_chunked.json"
INDEX_FILE_PATH = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising\\semantic_index.faiss"

# Load environment variables from .env file
load_dotenv()

# Debug print to check if the API key is loaded (partially masked for security)
api_key = os.getenv("OPENAI_API_KEY")
if api_key:
    print(f"Loaded API Key: {api_key[:4]}{'*' * (len(api_key) - 4)}")
else:
    print("API Key not found. Please check your .env file.")

# Instantiate the OpenAI client
client = OpenAI(api_key=api_key)

def build_index(json_file_path, index_file_path):
    """
    Builds a FAISS index from pre-chunked JSON data by generating embeddings for each chunk.

    Args:
        json_file_path (str): Path to the JSON file containing chunked data.
        index_file_path (str): Path to save the FAISS index.

    Returns:
        None
    """
    # Load the chunked JSON file
    try:
        with open(json_file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading the JSON file: {e}")
        return

    # Initialize FAISS index
    dimension = 1536  # Dimension of OpenAI embeddings
    index = faiss.IndexFlatL2(dimension)

    metadata_list = []  # Store metadata for each chunk

    for entry in data:
        filename = entry.get("filename")
        tags = entry.get("tags", [])
        metadata = entry.get("metadata", {})
        chunks = entry.get("chunks", [])  # Use pre-chunked text from the JSON

        for i, chunk in enumerate(chunks):
            max_retries = 3
            for attempt in range(max_retries):
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
                        "chunk_id": f"{filename}_chunk_{i}",
                        "tags": tags,
                        "metadata": metadata,
                        "text": chunk
                    })

                    break  # Exit retry loop on success
                except Exception as e:
                    print(f"Error embedding chunk {i} of {filename} on attempt {attempt + 1}: {e}")
                    if attempt < max_retries - 1:
                        print("Retrying...")
                else:
                    print(f"Failed to embed chunk {i} of {filename} after {max_retries} attempts.")
                    continue

    # Save FAISS index
    try:
        faiss.write_index(index, index_file_path)
        print(f"FAISS index saved to {index_file_path}")
    except Exception as e:
        print(f"Error saving FAISS index: {e}")

    # Save metadata as a JSON file
    metadata_file_path = os.path.splitext(index_file_path)[0] + "_metadata.json"
    try:
        with open(metadata_file_path, "w", encoding="utf-8") as f:
            json.dump(metadata_list, f, indent=4)
        print(f"Metadata saved to {metadata_file_path}")
    except Exception as e:
        print(f"Error saving metadata: {e}")

if __name__ == "__main__":
    """
    Main execution flow for building the FAISS index.
    """
    try:
        # First, chunk the text using the chunking script
        print("Starting the chunking process...")
        process_characters_and_chapters(CHARACTERS_FOLDER, CHAPTERS_FILE, CHUNKED_JSON_FILE_PATH, chunk_size=300)
        print("Chunking process completed successfully!")

        # Then, build the FAISS index using the chunked JSON
        print("Starting the FAISS index build process...")
        build_index(CHUNKED_JSON_FILE_PATH, INDEX_FILE_PATH)
        print("FAISS index built successfully!")
    except Exception as e:
        print(f"Error during the process: {e}")
