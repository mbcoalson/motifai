"""
Unit tests for tag_parser.py
"""
import pytest
from agent_utilities.fields.tag_parser import parse_query

def test_single_tag():
    query = "@character:Anais"
    expected = {"character": ["anais"]}
    assert parse_query(query) == expected

def test_multiple_tags():
    query = "@character:Anais @theme:Hope"
    expected = {"character": ["anais"], "theme": ["hope"]}
    assert parse_query(query) == expected

