import os
import shutil

# List of common paths where NLTK data might exist
nltk_common_paths = [
    os.path.expanduser("~/nltk_data"),  # User directory
    os.path.join(os.getcwd(), "nltk_data"),  # Current working directory
    os.path.expanduser("~/.nltk_data"),  # Hidden directory in home
    "C:\\Users\\mattc\\AppData\\Roaming\\nltk_data",  # AppData (Windows)
    "C:\\nltk_data",  # Root-level nltk_data (Windows)
    "D:\\nltk_data",  # Another drive example
    "E:\\nltk_data",  # Another drive example
]

# Function to check and optionally delete NLTK directories
def check_and_delete_nltk_dirs(delete=False):
    print("Checking for existing NLTK directories...")
    for path in nltk_common_paths:
        if os.path.exists(path):
            print(f"NLTK directory found: {path}")
            if delete:
                try:
                    shutil.rmtree(path)
                    print(f"Deleted: {path}")
                except Exception as e:
                    print(f"Error deleting {path}: {e}")
        else:
            print(f"No NLTK directory found at: {path}")

# Set delete=True to remove the directories
check_and_delete_nltk_dirs(delete=True)
