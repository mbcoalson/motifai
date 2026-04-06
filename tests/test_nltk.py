import nltk
from nltk.tokenize import sent_tokenize

nltk.download('punkt_tab')  # Ensure punkt is available
text = "This is a test sentence. Here's another one."
print(sent_tokenize(text))
