from bertopic import BERTopic
from sentence_transformers import SentenceTransformer
from typing import List, Dict, Any
import numpy as np


class TopicModeler:
    def __init__(self):
        """Initialize BERTopic with a lightweight sentence transformer"""
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')

        # Initialize BERTopic with custom settings for small datasets
        self.topic_model = BERTopic(
            embedding_model=self.embedding_model,
            min_topic_size=2,
            nr_topics="auto",
            calculate_probabilities=False,  # ✅ Changed to False for small datasets
            verbose=False,
            low_memory=True  # ✅ Added for efficiency
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
        # ✅ Increased minimum documents needed
        if not documents or len(documents) < 3:
            return {
                "topics": [],
                "document_topics": [],
                "topic_info": [],
                "error": "Need at least 3 documents for topic modeling"
            }

        try:
            # Fit the model and predict topics
            topics, _ = self.topic_model.fit_transform(documents)  # ✅ Removed probabilities

            # Get topic information
            topic_info = self.topic_model.get_topic_info()

            # Get top topics (excluding outlier topic -1)
            top_topics = topic_info[topic_info['Topic'] != -1].head(num_topics)

            # Format topics with their representative words
            formatted_topics = []
            for idx, row in top_topics.iterrows():
                topic_id = row['Topic']
                topic_words = self.topic_model.get_topic(topic_id)

                # Get top 5 words for this topic
                top_words = [word for word, _ in topic_words[:5]]

                formatted_topics.append({
                    "topic_id": int(topic_id),
                    "count": int(row['Count']),
                    "keywords": top_words,
                    "label": ", ".join(top_words[:3])
                })

            # Map documents to their topics
            document_topics = []
            for doc_idx, topic_id in enumerate(topics):
                if topic_id != -1:
                    topic_words = self.topic_model.get_topic(topic_id)
                    keywords = [word for word, _ in topic_words[:3]]

                    document_topics.append({
                        "document_index": doc_idx,
                        "topic_id": int(topic_id),
                        "topic_label": ", ".join(keywords),
                        "probability": 1.0  # ✅ Default probability since we disabled calc
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
                "total_documents": len(documents)
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
    """
    Extract topics from news articles

    Args:
        articles: List of article texts (title + description)
        num_topics: Number of topics to extract

    Returns:
        Dictionary with topics and assignments
    """
    return topic_modeler.extract_topics(articles, num_topics)
