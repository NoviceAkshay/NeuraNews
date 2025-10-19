import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from collections import Counter
from keybert import KeyBERT

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)

def preprocess_news(news_list):
    """
    Tokenize and clean news text.
    """
    stop_words = set(stopwords.words("english"))
    tokenized = []
    for doc in news_list:
        tokens = word_tokenize(doc.lower())
        clean = [w for w in tokens if w.isalpha() and w not in stop_words]
        tokenized.append(clean)
    return tokenized

def extract_topics(tokenized, num_topics=3, words_per_topic=5):
    """
    Extract 'topics' as top frequent words (simple fallback).
    """
    all_words = [word for doc in tokenized for word in doc]
    common_words = Counter(all_words).most_common(num_topics * words_per_topic)
    topics = []
    for i in range(num_topics):
        start = i * words_per_topic
        end = start + words_per_topic
        topics.append([word for word, _ in common_words[start:end]])
    return topics

def extract_keywords(articles, top_n=5):
    """
    Extract keywords using KeyBERT by combining title and description.
    articles: List of dicts with 'title' and 'description' keys.
    Returns a list of keyword lists per article.
    """
    kw_model = KeyBERT()
    keywords_per_article = []
    for article in articles:
        combined_text = f"{article.get('title', '')} {article.get('description', '')}".strip()
        keywords = kw_model.extract_keywords(
            combined_text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=top_n
        )
        keywords_per_article.append([kw[0] for kw in keywords])
    return keywords_per_article

def extract_keywords_from_texts(texts, top_n=5):
    """
    Extract keywords from list of raw text strings.
    """
    kw_model = KeyBERT()
    keywords_per_text = []
    for text in texts:
        keywords = kw_model.extract_keywords(
            text,
            keyphrase_ngram_range=(1, 2),
            stop_words='english',
            top_n=top_n
        )
        keywords_per_text.append([kw[0] for kw in keywords])
    return keywords_per_text
