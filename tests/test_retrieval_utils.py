import sys
import os
import pytest

# Ensure src/ is on the path so we can import project modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

# Import the function under test
from agent_utilities.retrieval_utils import retrieve_relevant_text

# ========== BASIC TESTS ==========

def test_pytest_sanity_check():
    """Sanity check to confirm pytest is working."""
    assert 2 + 2 == 4

# ========== HYBRID RETRIEVAL TESTS ==========

def test_retrieve_relevant_text_tag_only():
    """Ensure tag-based retrieval returns expected content or fallback."""
    query = "@character:Anais"
    result = retrieve_relevant_text(query, k=3)

    assert isinstance(result, str)
    assert "Anais" in result or result != "No relevant context found."

def test_retrieve_relevant_text_semantic_only():
    """Ensure semantic-only queries return coherent chunks."""
    query = "Tell me about the flooding and how people survived."
    result = retrieve_relevant_text(query, k=3)

    assert isinstance(result, str)
    assert result != "No relevant context found."

def test_retrieve_relevant_text_hybrid():
    """Ensure hybrid queries still return valid matches."""
    query = "@location:Florida Tell me how Anais survived the storm."
    result = retrieve_relevant_text(query, k=3)

    assert isinstance(result, str)
    assert "Anais" in result or "Florida" in result or result != "No relevant context found."