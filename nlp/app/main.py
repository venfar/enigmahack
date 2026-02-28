from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.core.config import settings
from app.core.logger import log
from app.api.routes import router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Инициализация при старте"""
    log.info("Запуск API сервера...")
    log.info(f"Host: {settings.host}:{settings.port}")
    yield
    log.info("Завершение работы API сервера")

app = FastAPI(
    title="Email Processing API",
    description="API для обработки писем техподдержки ЭРИС",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Роуты
app.include_router(router, prefix="/api/v1")

@app.get("/", tags=["Root"])
async def root():
    return {
        "message": "Email Processing API",
        "docs": "/docs",
        "health": "/api/v1/health"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level=settings.log_level.lower()
    )