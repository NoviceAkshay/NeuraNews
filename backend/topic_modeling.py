from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
import nltk
from nltk.corpus import stopwords

# Download stopwords only once (or move outside for performance)
nltk.download('stopwords')
stop_words = set(stopwords.words('english'))

def preprocess(text):
    # Lowercase and remove stopwords
    return " ".join([word for word in text.lower().split() if word not in stop_words])

class TopicModeler:
    def __init__(self):
        """Initialize BERTopic with a lightweight sentence transformer and custom vectorizer."""
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Use CountVectorizer with English stopwords
        vectorizer_model = CountVectorizer(stop_words='english', max_features=10000)

        self.topic_model = BERTopic(
            embedding_model=self.embedding_model,
            vectorizer_model=vectorizer_model,
            min_topic_size=2,
            nr_topics="auto",
            calculate_probabilities=False,
            verbose=False,
            low_memory=True
        )

    def extract_topics(self, documents: List[str], num_topics: int = 5) -> Dict[str, Any]:
        """
        Extract topics from a list of documents

        Args:
            documents: List of text documents (news articles)
            num_topics: Number of top topics to return

        Returns:
            Dictionary containing topics, document assignments, and topic info
        """
        # Preprocess each document to remove stopwords
        cleaned_docs = [preprocess(doc) for doc in documents]

        if not cleaned_docs or len(cleaned_docs) < 3:
            return {
                "topics": [],
                "document_topics": [],
                "topic_info": [],
                "error": "Need at least 3 documents for topic modeling"
            }

        try:
            topics, _ = self.topic_model.fit_transform(cleaned_docs)
            topic_info = self.topic_model.get_topic_info()
            top_topics = topic_info[topic_info['Topic'] != -1].head(num_topics)
            formatted_topics = []
            for idx, row in top_topics.iterrows():
                topic_id = row['Topic']
                topic_words = self.topic_model.get_topic(topic_id)
                top_words = [word for word, _ in topic_words[:5]]
                formatted_topics.append({
                    "topic_id": int(topic_id),
                    "count": int(row['Count']),
                    "keywords": top_words,
                    "label": ", ".join(top_words[:3])
                })
            document_topics = []
            for doc_idx, topic_id in enumerate(topics):
                if topic_id != -1:
                    topic_words = self.topic_model.get_topic(topic_id)
                    keywords = [word for word, _ in topic_words[:3]]
                    document_topics.append({
                        "document_index": doc_idx,
                        "topic_id": int(topic_id),
                        "topic_label": ", ".join(keywords),
                        "probability": 1.0
                    })
                else:
                    document_topics.append({
                        "document_index": doc_idx,
                        "topic_id": -1,
                        "topic_label": "Outlier",
                        "probability": 0.0
                    })
            return {
                "topics": formatted_topics,
                "document_topics": document_topics,
                "total_topics": len(formatted_topics),
                "total_documents": len(cleaned_docs)
            }
        except Exception as e:
            return {
                "topics": [],
                "document_topics": [],
                "topic_info": [],
                "error": f"Topic modeling failed: {str(e)}"
            }

# Global instance
topic_modeler = TopicModeler()

def get_topics_from_articles(articles: List[str], num_topics: int = 5) -> Dict[str, Any]:
    return topic_modeler.extract_topics(articles, num_topics)
