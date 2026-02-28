from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProcessedEmail(BaseModel):
    email_id: str
    date: Optional[str] = None
    fio: Optional[str] = None
    text: Optional[str] = None
    object_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    serial_numbers: List[str] = Field(default_factory=list)
    device_type: Optional[str] = None
    summary: Optional[str] = None
    sentiment: Optional[str] = None
    sentiment_confidence: Optional[float] = None
    category: Optional[str] = None
    category_confidence: Optional[float] = None
    processed_at: str
    response_body: Optional[str] = None
    response_subject: Optional[str] = None
    response_method: Optional[str] = None

    class Config:
        from_attributes = True

class HealthResponse(BaseModel):
    status: str
    timestamp: str
    models: dict

class StatsResponse(BaseModel):
    total_processed: int
    by_sentiment: dict
    by_category: dict
    last_updated: str