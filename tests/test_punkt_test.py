import nltk
from nltk.tokenize import sent_tokenize

# Explicitly set the path to nltk_data
nltk.data.path.append(r"C:\Users\mattc\AppData\Roaming\nltk_data")

# Test tokenization
text = "This is a test sentence. Here's another one. Let's confirm everything works!"
print(sent_tokenize(text))


