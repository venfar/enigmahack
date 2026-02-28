from dataclasses import dataclass, asdict
from typing import Optional, List
from datetime import datetime

@dataclass
class Ticket:
    email_id: str
    received_date: str
    fio: Optional[str]
    object_name: Optional[str]
    phone: Optional[str]
    email: str
    serial_numbers: str
    device_type: Optional[str]
    description: str
    sentiment: str
    sentiment_confidence: float
    category: str
    category_confidence: float
    processed_at: str
    is_answered: bool = False
    
    def to_dict(self) -> dict:
        """Преобразование в словарь"""
        return asdict(self)
    
    @classmethod
    def from_record(cls, record: dict) -> 'Ticket':
        import json
        return cls(
            email_id=record['email_id'],
            received_date=record['date'],
            fio=record['fio'],
            object_name=record['object_name'],
            phone=record['phone'],
            email=record['email'],
            serial_numbers=json.dumps(record.get('serial_numbers', []), ensure_ascii=False),
            device_type=record['device_type'],
            description=record['description'],
            sentiment=record['sentiment'],
            sentiment_confidence=record['sentiment_confidence'],
            category=record['category'],
            category_confidence=record['category_confidence'],
            processed_at=record['processed_at'],
            is_answered=False
        )