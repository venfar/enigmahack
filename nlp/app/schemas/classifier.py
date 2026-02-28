from pydantic import BaseModel, Field

class ClassifierRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=10000, description="Текст для анализа")

class ClassifierResponse(BaseModel):
    """Схема ответа с результатом категории"""
    category: str = Field(..., description="Категория")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Уверенность модели (0-1)")
    method: str = Field(..., description="Использованный метод")
    model_used: str = Field(..., description="Название использованной модели")
    

class HealthCheck(BaseModel):
    """Схема для проверки работоспособности"""
    status: str
    model_loaded: bool
    model_name: str