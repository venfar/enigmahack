from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class EmailMessage(BaseModel):
    """Модель письма для обработки"""
    id: str
    subject: str
    sender: str
    sender_name: Optional[str] = None
    date: datetime
    body: str
    attachments: List[str] = []