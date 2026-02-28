from transformers import pipeline
from app.core.config import settings
from app.core.logger import log
from app.models.base.classifier_keyword import keywords

class Classifier:
    def __init__(self):
        self.model_name = settings.classifier_name
        self.device = settings.device
        self.categories = list(keywords.keys())
        self.keywords = keywords
        
        self.pipeline = None
        self._load_model()

    def _load_model(self):
        log.info(f"Загрузка классификатора {self.model_name} на устройство {self.device}...")
        try:
            self.pipeline = pipeline(
                "zero-shot-classification",
                model=self.model_name,
                tokenizer=self.model_name,
                device=-1 if self.device == "cpu" else 0,
                hypothesis_template="Это запрос в категорию {}.",
                multi_label=False
            )
            log.success(f"Классификатор {self.model_name} успешно загружен")
        except Exception as e:
            log.error(f"Ошибка загрузки классификатора: {e}")
            self.pipeline = None

    def _classify_by_keywords(self, text: str, subject: str = "") -> tuple:
        """Классификация по ключевым словам"""
        combined = (subject + " " + text).lower()
        
        best_category = "другое"
        best_score = 0.0
        
        for category, words in self.keywords.items():
            matches = sum(1 for word in words if word in combined)
            if matches > 0:
                score = min(matches / 3.0, 1.0)  # 3+ совпадения = 100%
                if score > best_score:
                    best_score = score
                    best_category = category
        
        return best_category, best_score, "keywords"

    def _classify_by_model(self, text: str, subject: str = "") -> tuple:
        """Классификация через zero-shot модель"""
        if not self.pipeline:
            return "другое", 0.2, "fallback"
        
        try:
            input_text = f"{subject} {text}"[:512]
            result = self.pipeline(input_text, candidate_labels=self.categories)
            
            label = result['labels'][0]
            score = result['scores'][0]
            
            return label, score, "model"
        except Exception as e:
            log.error(f"Ошибка модели: {e}")
            return "другое", 0.2, "fallback"

    def predict(self, text: str, subject: str = "") -> dict:
        """
        Гибридная классификация:
        1. Сначала keywords (быстро и точно при совпадении)
        2. Если keywords не дали уверенности — модель
        3. Возвращаем лучший результат
        """
        kw_category, kw_score, kw_method = self._classify_by_keywords(text, subject)
        
        if kw_score >= 0.5:
            log.debug(f"Классификация по keywords: {kw_category} ({kw_score:.2%})")
            return {
                'category': kw_category,
                'confidence': round(kw_score, 4),
                'method': 'keywords'
            }
        
        model_category, model_score, model_method = self._classify_by_model(text, subject)
        
        if model_score > kw_score:
            log.debug(f"Классификация по модели: {model_category} ({model_score:.2%})")
            return {
                'category': model_category,
                'confidence': round(model_score, 4),
                'method': 'model'
            }
        else:
            log.debug(f" Классификация по keywords (fallback): {kw_category} ({kw_score:.2%})")
            return {
                'category': kw_category,
                'confidence': round(kw_score, 4),
                'method': 'keywords'
            }

    def __call__(self, text: str, subject: str = "") -> dict:
        return self.predict(text, subject)