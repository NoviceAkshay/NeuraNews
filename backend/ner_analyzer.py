from transformers import AutoTokenizer, AutoModelForTokenClassification, pipeline

class NewsNerAnalyzer:
    def __init__(self):
        self.ner_pipeline = pipeline(
            "ner",
            model="dslim/bert-base-NER",
            tokenizer="dslim/bert-base-NER",
            aggregation_strategy="simple"  # so entities are combined, not split!
        )

    def extract_entities(self, text):
        return self.ner_pipeline(text)

    def batch_extract_entities(self, texts):
        return [self.ner_pipeline(txt) for txt in texts]
