import nltk
from nltk.tokenize import sent_tokenize

# Explicitly set the NLTK data path
nltk.data.path.append(r"C:\Users\mattc\AppData\Roaming\nltk_data")

# Test tokenization
text = "This is a test sentence. Here's another sentence. Let's confirm everything works!"
try:
    print(sent_tokenize(text))
except Exception as e:
    print(f"Error during tokenization: {e}")
