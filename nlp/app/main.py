from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status
from app.schemas.sentiment import SentimentRequest, SentimentResponse, HealthCheck
from app.models.sentiment_model import SentimentAnalyzer
from app.core.config import settings
from app.core.logger import log


analyzer = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    global analyzer
    log.info("Инициализация сервиса анализа тональности...")
    try:
        analyzer = SentimentAnalyzer()
        log.info("Сервис готов к работе")
    except Exception as e:
        log.error(f"Не удалось загрузить модель: {e}")
        analyzer = None
    yield
    log.info("Завершение работы сервиса")

app = FastAPI(
    title="Analysis Service",
    description="API",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/", tags=["Root"])
async def root():
    return {"message": "Analysis Service is running. Go to /docs for documentation."}

@app.get("/health", response_model=HealthCheck, tags=["Health"])
async def health_check():
    if analyzer is None:
        return HealthCheck(
            status="error",
            model_loaded=False,
            model_name=settings.model_name
        )
    return HealthCheck(
        status="ok",
        model_loaded=True,
        model_name=settings.model_name
    )

@app.post("/sentiment", response_model=SentimentResponse, tags=["Sentiment"])
async def analyze_sentiment(request: SentimentRequest):
    if analyzer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Please try again later."
        )
    try:
        result = analyzer.predict(request.text)
        return SentimentResponse(
            sentiment=result['sentiment'],
            confidence=result['confidence'],
            model_used=settings.model_name
        )
    except Exception as e:
        log.error(f"Ошибка обработки запроса: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during prediction"
        )

'''@app.post("/category", response_model=SentimentResponse, tags=["category"])
async def analyze_category(request: SentimentRequest):
    if analyzer is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Model not loaded. Please try again later."
        )
    try:
        result = analyzer.predict(request.text)
        return SentimentResponse(
            sentiment=result['sentiment'],
            confidence=result['confidence'],
            model_used=settings.model_name
        )
    except Exception as e:
        log.error(f"Ошибка обработки запроса: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error during prediction"
        )
    '''

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower()
    )