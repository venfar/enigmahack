from pydantic import BaseModel, Field

class SentimentRequest(BaseModel):
    """Схема запроса на анализ тональности"""
    text: str = Field(..., min_length=1, max_length=10000, description="Текст для анализа")

class SentimentResponse(BaseModel):
    """Схема ответа с результатом анализа"""
    sentiment: str = Field(..., description="Тональность: positive/neutral/negative")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Уверенность модели (0-1)")
    model_used: str = Field(..., description="Название использованной модели")

class HealthCheck(BaseModel):
    """Схема для проверки работоспособности"""
    status: str
    model_loaded: bool
    model_name: str