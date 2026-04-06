import faiss
import numpy as np
import json

# Paths to the index and metadata files
INDEX_FILE_PATH = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising\\semantic_index.faiss"
METADATA_FILE_PATH = r"C:\\Users\\mattc\\OneDrive\\Desktop\\Obsidian\\Path\\Water_Rising\\semantic_index_metadata.json"

def load_index_and_metadata():
    """Load the FAISS index and metadata."""
    index = faiss.read_index(INDEX_FILE_PATH)
    with open(METADATA_FILE_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    return index, metadata

def query_index(query_vector, k=5):
    """
    Query the FAISS index and return the top-k results.

    Args:
        query_vector (np.array): The vector representing the query.
        k (int): Number of top results to return.

    Returns:
        list: Top-k matching metadata entries.
    """
    index, metadata = load_index_and_metadata()
    distances, indices = index.search(np.array([query_vector], dtype='float32'), k=k)

    results = []
    for dist, idx in zip(distances[0], indices[0]):
        if 0 <= idx < len(metadata):
            entry = metadata[idx]
            entry["distance"] = dist
            results.append(entry)
        else:
            print(f"Warning: Index {idx} out of bounds.")
    
    return results

# Example usage:
if __name__ == "__main__":
    # Replace this with an actual embedding vector when available
    query_vector = np.random.rand(1536).astype('float32')
    results = query_index(query_vector)
    
    print("Top matching results:")
    for result in results:
        print(f"Chunk ID: {result['chunk_id']}, Distance: {result['distance']}")
        print(f"Text: {result['text']}\n")
