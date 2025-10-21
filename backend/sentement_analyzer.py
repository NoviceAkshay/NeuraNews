from transformers import pipeline

class NewsSentimentEmotionAnalyzer:
    def __init__(self):
        # For standard sentiment (positive/negative/neutral)
        self.sentiment_analyzer = pipeline(
            "sentiment-analysis",
            model="cardiffnlp/twitter-roberta-base-sentiment-latest"
        )
        # For emotion (can be added in step 4)
        # self.emotion_analyzer = pipeline(
        #     "text-classification",
        #     model="j-hartmann/emotion-english-distilroberta-base"
        # )

    def analyze_sentiment(self, text):
        return self.sentiment_analyzer(text)[0]

    def batch_analyze_sentiment(self, texts):
        return self.sentiment_analyzer(texts)
