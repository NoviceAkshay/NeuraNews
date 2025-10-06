import re
import string
import spacy
from textblob import TextBlob
from nltk.corpus import stopwords
import nltk
from rapidfuzz import fuzz

# Download stopwords if not already
nltk.download("stopwords")
stop_words = set(stopwords.words("english"))

# Load spaCy English model
nlp = spacy.load("en_core_web_sm")

def preprocess_text(text: str) -> dict:
    original_text = text

    # 1. Lowercase
    text = text.lower()

    # 2. Remove URLs & HTML
    text = re.sub(r"http\S+|www\S+|<.*?>", "", text)

    # 3. Remove numbers & punctuation
    text = re.sub(r"\d+", "", text)
    text = text.translate(str.maketrans("", "", string.punctuation))

    # 4. Spell correction
    corrected = str(TextBlob(text).correct())

    # 5. Tokenization + Lemmatization
    doc = nlp(corrected)
    tokens = [
        token.lemma_ for token in doc
        if token.lemma_ not in stop_words and not token.is_punct and not token.is_space
    ]
    cleaned = " ".join(tokens)

    # 6. Fuzzy similarity
    similarity = fuzz.ratio(original_text.lower(), cleaned.lower())

    suggestion = None
    if similarity < 80:  # threshold: less than 80% similarity
        suggestion = cleaned

    return {
        "original": original_text,
        "cleaned": cleaned,
        "suggestion": suggestion
    }












