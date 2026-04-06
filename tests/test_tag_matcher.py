"""
Unit tests for tag_matcher.py
"""
from agent_utilities.fields.tag_matcher import apply_filters

def test_filter_by_character():
    filters = {"character": ["anais"]}
    metadata = [
        {"metadata": {"characters": ["[[Anais Non]]"]}, "body": "Text A"},
        {"metadata": {"characters": ["[[Joseph Krutz]]"]}, "body": "Text B"},
    ]
    result = apply_filters(filters, metadata)
    assert len(result) == 1
    assert result[0]["body"] == "Text A"

def test_filter_by_multiple_values_or_logic():
    """Chunks should match if any value for a tag is present."""
    filters = {"character": ["anais", "joseph"]}
    metadata = [
        {"metadata": {"characters": ["[[Anais Non]]"]}, "body": "Text A"},
        {"metadata": {"characters": ["[[Joseph Krutz]]"]}, "body": "Text B"},
    ]
    result = apply_filters(filters, metadata)
    bodies = {chunk["body"] for chunk in result}
    assert bodies == {"Text A", "Text B"}
