from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from datetime import datetime
import json
import os

from app.core.config import settings
from app.core.logger import log
from app.schemas.support_ticket import ProcessedEmail, HealthResponse, StatsResponse
from app.models.sentiment_model import SentimentAnalyzer
from app.models.classifier_model import Classifier

router = APIRouter()

def load_records() -> List[dict]:
    """Загрузка обработанных записей"""
    if os.path.exists(settings.records_file):
        try:
            with open(settings.records_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            log.error(f"Ошибка загрузки записей: {e}")
    return []

@router.get("/health", response_model=HealthResponse, tags=["System"])
async def health_check():
    """Проверка здоровья API"""
    models_status = {}
    try:
        SentimentAnalyzer()
        models_status['sentiment'] = 'ok'
    except:
        models_status['sentiment'] = 'error'
    
    try:
        Classifier()
        models_status['classifier'] = 'ok'
    except:
        models_status['classifier'] = 'error'
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        models=models_status
    )

@router.get("/tickets", response_model=List[ProcessedEmail], tags=["Tickets"])
async def get_tickets(
    limit: int = Query(50, ge=1, le=500),
    sentiment: Optional[str] = Query(None),
    category: Optional[str] = Query(None),
    search: Optional[str] = Query(None)
):
    """Получение обработанных обращений с фильтрацией"""
    records = load_records()
    
    # Фильтрация
    if sentiment:
        records = [r for r in records if r.get('sentiment') == sentiment]
    if category:
        records = [r for r in records if r.get('category') == category]
    if search:
        search_lower = search.lower()
        records = [r for r in records if 
                   search_lower in str(r.get('description', '')).lower() or
                   search_lower in str(r.get('fio', '')).lower() or
                   search_lower in str(r.get('object_name', '')).lower()]
    
    # Сортировка по дате (новые сначала)
    records.sort(key=lambda x: x.get('processed_at', ''), reverse=True)
    
    return [ProcessedEmail(**r) for r in records[:limit]]

@router.get("/tickets/{email_id}", response_model=ProcessedEmail, tags=["Tickets"])
async def get_ticket(email_id: str):
    """Получение конкретного обращения по ID"""
    records = load_records()
    for record in records:
        if record.get('email_id') == email_id:
            return ProcessedEmail(**record)
    raise HTTPException(status_code=404, detail="Обращение не найдено")

@router.get("/stats", response_model=StatsResponse, tags=["Analytics"])
async def get_stats():
    """Статистика обработанных обращений"""
    records = load_records()
    
    by_sentiment = {}
    by_category = {}
    
    for r in records:
        sent = r.get('sentiment', 'unknown')
        cat = r.get('category', 'unknown')
        by_sentiment[sent] = by_sentiment.get(sent, 0) + 1
        by_category[cat] = by_category.get(cat, 0) + 1
    
    return StatsResponse(
        total_processed=len(records),
        by_sentiment=by_sentiment,
        by_category=by_category,
        last_updated=datetime.now().isoformat()
    )

@router.post("/tickets/{email_id}/response", tags=["Tickets"])
async def get_response(email_id: str):
    """Получение сгенерированного ответа для обращения"""
    records = load_records()
    for record in records:
        if record.get('email_id') == email_id:
            return {
                'subject': record.get('response_subject'),
                'body': record.get('response_body'),
                'method': record.get('response_method')
            }
    raise HTTPException(status_code=404, detail="Обращение не найдено")