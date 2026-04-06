# To call:
# from agent_utilities.retrieval_utils import retrieve_relevant_text
# retrieved_text = retrieve_relevant_text("Tell me about @character:John")

import faiss
import json
import numpy as np

from agent_utilities.embedding_utils import embed_query
from agent_utilities.tag_utils import tag_filter


def load_faiss_index():
    """
    Loads FAISS index and corresponding metadata.
    Assumes files are located in the project's 'data/' directory.
    """
    index = faiss.read_index("data/faiss_index.pkl")
    with open("data/faiss_index_metadata.json", "r", encoding="utf-8") as f:
        metadata = json.load(f)
    return index, metadata


# Load once at import
faiss_index, faiss_metadata = load_faiss_index()


def retrieve_relevant_text(query: str, k: int = 3) -> str:
    """
    Hybrid retrieval function:
    - Uses FAISS for semantic similarity.
    - Uses tag-based filtering if '@' tags are present in query.

    Combines both types of results, deduplicates, and returns the most relevant text.
    """
    query_vector = embed_query(query)
    query_vector_np = np.array([query_vector]).astype(np.float32)

    # FAISS Semantic Search
    distances, indices = faiss_index.search(query_vector_np, k)
    valid_indices = [idx for idx in indices[0] if idx != -1]
    faiss_chunks = [faiss_metadata[idx] for idx in valid_indices]

    # Tag-Based Filtering (if applicable)
    tag_chunks = tag_filter(query, faiss_metadata) if "@" in query else []

    # Combine & Deduplicate
    seen_texts = set()
    combined_chunks = []

    for chunk in tag_chunks + faiss_chunks:
        text = chunk.get("text", "")
        if text and text not in seen_texts:
            combined_chunks.append(text)
            seen_texts.add(text)

    return "\n".join(combined_chunks) if combined_chunks else "No relevant context found."
