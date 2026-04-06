"""
Extract @key:value filters from user input.
Supports multiple filters per query.

See: vision.md
"""

import re

def parse_query(query: str) -> dict:
    pattern = r"@(?P<key>\w+):(?P<value>[\w#\[\] ]+)"
    matches = re.findall(pattern, query)
    filters = {}
    for key, value in matches:
        key = key.lower()
        value = value.strip().lower()
        if key in filters:
            filters[key].append(value)
        else:
            filters[key] = [value]
    return filters
