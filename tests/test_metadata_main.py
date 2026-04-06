"""
Integration test for metadata_main.py
"""
from agent_utilities.metadata_main import filter_by_tag

def test_filter_by_tag_integration():
    query = "@tone:Gritty"
    metadata = [
        {"metadata": {"tone": "Gritty"}, "body": "Scene with tension."},
        {"metadata": {"tone": "Hopeful"}, "body": "Scene with light."},
    ]
    result = filter_by_tag(query, metadata)
    assert len(result) == 1
    assert result[0]["metadata"]["tone"] == "Gritty"
