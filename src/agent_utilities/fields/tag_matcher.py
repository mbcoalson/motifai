"""
Applies fuzzy matching for parsed filters against metadata chunks.
Supports partial string matching and strips Obsidian [[links]].

See: vision.md
"""


import re

def normalize_text(text):
    text = text.lower()
    text = re.sub(r"\[\[|\]\]", "", text)
    return text

def matches_filter(value_list, target):
    target = normalize_text(target)
    return any(normalize_text(val) in target for val in value_list)

def apply_filters(filters: dict, metadata_chunks: list) -> list:
    """Return chunks whose metadata matches the provided filters."""
    filtered_chunks = []

    alias_map = {
        "character": "characters",
        "theme": "themes",
        "tag": "tags",
    }

    for chunk in metadata_chunks:
        metadata = chunk.get("metadata", {})
        chunk_matches = True

        for key, values in filters.items():
            # Support singular keys by mapping to their plural metadata fields
            field_name = key
            if key not in metadata:
                field_name = alias_map.get(key, key)

            field = metadata.get(field_name, [])
            items = field if isinstance(field, list) else [field]

            # Require any value for this key to match any metadata item
            if not any(
                matches_filter([value], str(item))
                for value in values
                for item in items
            ):
                chunk_matches = False
                break

        if chunk_matches:
            filtered_chunks.append(chunk)

    return filtered_chunks
