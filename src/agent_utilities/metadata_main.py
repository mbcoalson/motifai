"""
Entrypoint for hybrid metadata filtering.

This module parses the user query for @key:value filters
and applies fuzzy matching logic to metadata chunks.

See: vision.md
"""



from agent_utilities.fields.tag_parser import parse_query
from agent_utilities.fields.tag_matcher import apply_filters

def filter_by_tag(query: str, metadata_chunks: list) -> list:
    filters = parse_query(query)
    if not filters:
        return []  # No explicit metadata filters found
    return apply_filters(filters, metadata_chunks)
