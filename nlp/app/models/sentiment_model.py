import torch
from transformers import pipeline, AutoModelForSequenceClassification, AutoTokenizer
from app.core.config import settings
from app.core.logger import log

class SentimentAnalyzer:
    def __init__(self):
        self.model_name = settings.model_name
        self.device = settings.device
        self.max_length = settings.max_length
        self.pipeline = None
        self._load_model()

    def _load_model(self):
        log.info(f"Загрузка модели {self.model_name} на устройство {self.device}...")
        try:
            self.pipeline = pipeline(
                "sentiment-analysis",
                model=self.model_name,
                tokenizer=self.model_name,
                device=self.device if self.device == "cuda" else -1,
                max_length=self.max_length,
                truncation=True
            )
            log.success(f"Модель {self.model_name} успешно загружена")
        except Exception as e:
            log.error(f"Ошибка загрузки модели: {e}")
            raise RuntimeError(f"Не удалось загрузить модель: {e}")

    def predict(self, text: str) -> dict:
        if not self.pipeline:
            raise RuntimeError("Модель не загружена")
        try:
            result = self.pipeline(text[:self.max_length])[0]
            label = result['label']
            score = result['score']

            # rubert-base-cased-sentiment: LABEL_0=negative, LABEL_1=neutral, LABEL_2=positive
            if label == 'LABEL_0':
                sentiment = 'negative'
            elif label == 'LABEL_1':
                sentiment = 'neutral'
            elif label == 'LABEL_2':
                sentiment = 'positive'
            else:
                sentiment = label.lower()

            return {
                'sentiment': sentiment,
                'confidence': round(score, 4)
            }
        except Exception as e:
            log.error(f"Ошибка при предсказании: {e}")
            raise

    def __call__(self, text: str) -> dict:
        return self.predict(text)