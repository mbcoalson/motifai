import os
import pytest
import faiss
import json
import numpy as np

# Hard-coded paths (adjust if needed).
INDEX_FILE_PATH = r"C:\Users\mattc\OneDrive\Desktop\Obsidian\Path\Water_Rising\semantic_index.faiss"
METADATA_FILE_PATH = r"C:\Users\mattc\OneDrive\Desktop\Obsidian\Path\Water_Rising\semantic_index_metadata.json"

def test_faiss_index_verification():
    """
    Validates the FAISS index size and consistency, then performs a sample query.
    Skips if the FAISS or metadata file is not found.
    """
    if not os.path.isfile(INDEX_FILE_PATH):
        pytest.skip(f"FAISS index file not found at {INDEX_FILE_PATH}, skipping test.")
    if not os.path.isfile(METADATA_FILE_PATH):
        pytest.skip(f"Metadata file not found at {METADATA_FILE_PATH}, skipping test.")

    # Load the FAISS index
    index = faiss.read_index(INDEX_FILE_PATH)

    # Load the metadata
    with open(METADATA_FILE_PATH, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Now run our validations
    validate_index_size(index, metadata)
    validate_data_consistency(index, metadata)
    perform_query_test(index, metadata, k=5)

def validate_index_size(index, metadata):
    """
    Ensure the number of vectors in the FAISS index matches the metadata entries.
    """
    index_size = index.ntotal
    metadata_size = len(metadata)

    assert index_size == metadata_size, (
        f"Index size ({index_size}) from {INDEX_FILE_PATH} "
        f"does not match metadata size ({metadata_size}) "
        f"from {METADATA_FILE_PATH}."
    )
    print(f"Index size validation passed: {index_size} vectors.")

def validate_data_consistency(index, metadata):
    """
    Ensure each index entry maps back to a valid metadata entry.
    """
    num_vectors = index.ntotal
    for i, metadata_entry in enumerate(metadata):
        assert "chunk_id" in metadata_entry, f"Metadata entry {i} missing 'chunk_id'."
        assert "text" in metadata_entry,    f"Metadata entry {i} missing 'text'."
    print(f"Data consistency validation passed for {num_vectors} entries.")

def perform_query_test(index, metadata, k=5):
    """
    Perform a sample query to validate that the index returns valid results.
    """
    # Example query vector (use real embeddings or a random vector).
    # Adjust dimension as needed if your index is not 1536.
    np.random.seed(42)  
    query_vector = np.random.rand(1536).astype("float32")

    # Search top-K
    distances, indices = index.search(np.array([query_vector]), k=k)

    print("Query Results:")
    for dist, idx in zip(distances[0], indices[0]):
        if 0 <= idx < len(metadata):
            print(f" - Metadata[{idx}]: Chunk ID = {metadata[idx]['chunk_id']}, Distance = {dist}")
        else:
            print(" - Invalid result (index out of bounds).")



