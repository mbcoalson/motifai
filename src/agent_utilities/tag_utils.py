# To use:
# from agent_utilities.tag_utils import tag_filter
# tagged_results = tag_filter("@character:John", faiss_metadata)


from agent_utilities.metadata_main import filter_by_tag


def tag_filter(query: str, metadata: list) -> list:
    """Return metadata chunks matching any explicit @tag filters in the query."""
    if "@" not in query:
        return []

    return filter_by_tag(query, metadata)

