def validate_chapters(file_path):
    # Load the JSON file
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"Error reading the JSON file: {e}")
        return

    errors = []
    warnings = []
    total_entries = len(data)

    required_metadata_fields = ['tags', 'chapter_id']  # Required for semantic search

    for chapter in data:
        filename = chapter.get("filename", "Unknown File")
        metadata = chapter.get("metadata", {})
        body = chapter.get("body", "")

        # Validate filename
        if not filename or not filename.endswith(".md"):
            errors.append(f"{filename}: Invalid or missing filename.")

        # Validate metadata
        if not isinstance(metadata, dict):
            errors.append(f"{filename}: Metadata is not a dictionary. Found: {metadata}")
        else:
            # Auto-generate chapter_id if missing
            if 'chapter_id' not in metadata:
                # Attempt to extract 'title' or use filename
                title = metadata.get('title', filename.replace(".md", "").strip())
                metadata['chapter_id'] = title
                warnings.append(f"{filename}: Missing 'chapter_id'. Auto-assigned as '{title}'.")

            # Validate required metadata fields
            for field in required_metadata_fields:
                if field not in metadata:
                    errors.append(f"{filename}: Missing '{field}' in metadata.")

        # Validate body
        if not body.strip():
            errors.append(f"{filename}: Missing or empty body.")
        elif len(body.split()) < 50:  # Example threshold: 50 words
            warnings.append(f"{filename}: Body content may be too short for effective chunking. Words: {len(body.split())}")

        # Check 'tags' field specifically for semantic search compatibility
        tags = metadata.get("tags", None)
        if not tags or not isinstance(tags, list):
            warnings.append(f"{filename}: 'tags' should be a non-empty list.")

    # Save updates back to JSON
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
        print(f"Auto-corrections saved to {file_path}")
    except Exception as e:
        print(f"Error saving updated JSON file: {e}")

    # Print the validation results
    print("=" * 80)
    print(f"Validation Summary for {file_path}")
    print(f"Total Entries: {total_entries}")
    print(f"Errors Found: {len(errors)}")
    print(f"Warnings Found: {len(warnings)}")
    print("=" * 80)

    if errors:
        print("Errors:")
        for error in errors:
            print(f"- {error}")

    if warnings:
        print("\nWarnings:")
        for warning in warnings:
            print(f"- {warning}")

    if not errors and not warnings:
        print("All entries are valid!")
    print("=" * 80)


