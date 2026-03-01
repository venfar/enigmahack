"""
Database Writer для сохранения обработанных писем в MySQL
"""

import mysql.connector
from mysql.connector import Error, pooling
from typing import Optional, Dict, List
from datetime import datetime
import re

from app.core.config import settings
from app.core.logger import log


class DatabaseWriter:
    """
    Менеджер записи данных в базу данных MySQL
    Использует connection pooling для эффективности
    """
    
    # Пул соединений (создаётся один раз при импорте модуля)
    _connection_pool: Optional[pooling.MySQLConnectionPool] = None
    
    @classmethod
    def _get_pool(cls) -> pooling.MySQLConnectionPool:
        """Получение или создание пула соединений"""
        if cls._connection_pool is None:
            try:
                cls._connection_pool = pooling.MySQLConnectionPool(
                    pool_name="eris_pool",
                    pool_size=5,
                    pool_reset_session=True,
                    host=settings.db_host,
                    port=3306,
                    user=settings.db_user,
                    password=settings.db_pass,
                    database=settings.db_name,
                    charset='utf8mb4',
                    use_unicode=True
                )
                log.success("✅ Пул соединений с БД создан")
            except Error as e:
                log.error(f"❌ Ошибка создания пула БД: {e}")
                raise
        return cls._connection_pool
    
    @classmethod
    def save_ticket(cls, record: Dict) -> Optional[int]:
        """
        Сохранение обработанного письма в таблицу ticket
        
        Args:
            record: Dict с данными из EmailWorker.process_email()
            
        Returns:
            int: ID созданной записи или None при ошибке
        """
        try:
            conn = cls._get_pool().get_connection()
            cursor = conn.cursor()
            
            # 1. Сохранение или получение Facility (объект)
            facility_id = cls._get_or_create_facility(cursor, record.get('object_name'))
            
            # 2. Сохранение или получение Contacts (контакты)
            contact_id = cls._get_or_create_contact(
                cursor, 
                record.get('fio'),
                record.get('email'),
                record.get('phone')
            )
            
            # 3. Получение ID sentiment и category из справочников
            sentiment_id = cls._get_sentiment_id(cursor, record.get('sentiment'))
            category_id = cls._get_category_id(cursor, record.get('category'))
            
            # 4. Сохранение газоанализатора (если указан)
            gas_analyzer_id = None
            if record.get('device_type') or record.get('serial_numbers'):
                gas_analyzer_id = cls._get_or_create_gas_analyzer(
                    cursor,
                    record.get('device_type'),
                    record.get('serial_numbers', [])
                )
            
            # 5. Основная запись в ticket
            query = """
                INSERT INTO ticket (
                    email_id, subject, body, facility_id, contact_id,
                    sentiment_id, sentiment_confidence, category_id, category_confidence,
                    gaz_analyzer_id, generated_response, response_method, status, created_at
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            
            # Извлечение subject из текста письма (первая строка или email_id)
            subject = cls._extract_subject(record.get('text', '')) or record.get('email_id', '')
            
            values = (
                record.get('email_id'),
                subject[:255],  # Ограничение VARCHAR(255)
                record.get('text'),  # MEDIUMTEXT
                facility_id,
                contact_id,
                sentiment_id,
                record.get('sentiment_confidence'),
                category_id,
                record.get('category_confidence'),
                gas_analyzer_id,
                record.get('response_body'),  # MEDIUMTEXT
                record.get('response_method'),
                'processed',  # Статус после успешной записи
                record.get('processed_at') or datetime.now()
            )
            
            cursor.execute(query, values)
            conn.commit()
            
            ticket_id = cursor.lastrowid
            log.info(f"💾 Запись сохранена: ticket_id={ticket_id}, email_id={record.get('email_id')}")
            
            return ticket_id
            
        except Error as e:
            log.error(f"❌ Ошибка записи в БД: {e}")
            if conn:
                conn.rollback()
            return None
            
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()
    
    @classmethod
    def _get_or_create_facility(cls, cursor, name: Optional[str]) -> Optional[int]:
        """Получение или создание записи Facility"""
        if not name:
            return None
        
        # Поиск существующего
        cursor.execute("SELECT id FROM Facility WHERE name = %s", (name,))
        result = cursor.fetchone()
        if result:
            return result[0]
        
        # Создание нового
        try:
            cursor.execute("INSERT INTO Facility (name) VALUES (%s)", (name,))
            return cursor.lastrowid
        except Error:
            return None  # Игнорируем дубликаты при конкурентной записи
    
    @classmethod
    def _get_or_create_contact(cls, cursor, full_name: Optional[str], 
                               email: Optional[str], phone: Optional[str]) -> Optional[int]:
        """Получение или создание записи Contacts"""
        if not full_name and not email:
            return None
        
        # Поиск по email (уникальный идентификатор)
        if email:
            cursor.execute("SELECT id FROM Contacts WHERE email = %s", (email,))
            result = cursor.fetchone()
            if result:
                return result[0]
        
        # Поиск по имени + телефону
        if full_name and phone:
            cursor.execute(
                "SELECT id FROM Contacts WHERE full_name = %s AND phone = %s", 
                (full_name, phone)
            )
            result = cursor.fetchone()
            if result:
                return result[0]
        
        # Создание нового
        try:
            cursor.execute(
                "INSERT INTO Contacts (full_name, email, phone) VALUES (%s, %s, %s)",
                (full_name or 'Неизвестный', email, phone)
            )
            return cursor.lastrowid
        except Error:
            return None
    
    @classmethod
    def _get_sentiment_id(cls, cursor, sentiment: Optional[str]) -> Optional[int]:
        """Получение ID тональности из справочника"""
        if not sentiment:
            return None
        
        sentiment_map = {
            'negative': 1,
            'neutral': 2, 
            'positive': 3
        }
        
        sentiment_key = sentiment.lower() if isinstance(sentiment, str) else None
        if sentiment_key in sentiment_map:
            return sentiment_map[sentiment_key]
        
        # Попытка найти в БД
        cursor.execute("SELECT id FROM Sentiment WHERE name = %s", (sentiment,))
        result = cursor.fetchone()
        return result[0] if result else 2  # Default: neutral
    
    @classmethod
    def _get_category_id(cls, cursor, category: Optional[str]) -> Optional[int]:
        """Получение ID категории из справочника"""
        if not category:
            return None
        
        category_map = {
            'документация': 1,
            'калибровка': 2,
            'техподдержка': 3,
            'подключение': 3,  # Маппинг на техподдержку
            'неисправность': 3,
            'гарантия': 3
        }
        
        category_key = category.lower() if isinstance(category, str) else None
        if category_key in category_map:
            return category_map[category_key]
        
        # Попытка найти в БД
        cursor.execute("SELECT id FROM Categories WHERE name = %s", (category,))
        result = cursor.fetchone()
        return result[0] if result else 3  # Default: техподдержка
    
    @classmethod
    def _get_or_create_gas_analyzer(cls, cursor, device_type: Optional[str], 
                                    serial_numbers: List[str]) -> Optional[int]:
        """Получение или создание записи Gas_analyzer"""
        # Приоритет: серийный номер > тип устройства
        serial = serial_numbers[0] if serial_numbers else None
        
        if serial:
            cursor.execute("SELECT id FROM Gas_analyzer WHERE serial_number = %s", (serial,))
            result = cursor.fetchone()
            if result:
                return result[0]
            
            # Определение type_id по названию устройства
            type_id = cls._get_gas_analyzer_type_id(cursor, device_type)
            
            try:
                cursor.execute(
                    "INSERT INTO Gas_analyzer (serial_number, type_id) VALUES (%s, %s)",
                    (serial, type_id)
                )
                return cursor.lastrowid
            except Error:
                return None
        
        return None
    
    @classmethod
    def _get_gas_analyzer_type_id(cls, cursor, device_type: Optional[str]) -> Optional[int]:
        """Получение ID типа газоанализатора"""
        if not device_type:
            return None
        
        type_map = {
            'дгс эрис-230': 1,
            'дгс эрис-210': 1,
            'пкг эрис-411': 2,
            'пг эрис-411': 2,
            'пг эрис-414': 2,
            'стационарный': 3,
            'переносной': 2
        }
        
        device_lower = str(device_type).lower() if device_type else ''
        for key, type_id in type_map.items():
            if key in device_lower:
                return type_id
        
        return 3  # Default: стационарный
    
    @classmethod
    def _extract_subject(cls, text: str) -> Optional[str]:
        """Извлечение темы из текста письма"""
        if not text:
            return None
        
        # Первая непустая строка как тема
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            subject = lines[0]
            # Удаление маркеров формата
            subject = re.sub(r'^[\*\#\-]+\s*', '', subject)
            return subject[:255] if len(subject) > 255 else subject
        
        return None
    
    @classmethod
    def bulk_save(cls, records: List[Dict]) -> Dict[str, int]:
        """
        Массовое сохранение записей
        
        Returns:
            Dict со статистикой: {"saved": N, "failed": M}
        """
        stats = {"saved": 0, "failed": 0}
        
        for record in records:
            ticket_id = cls.save_ticket(record)
            if ticket_id:
                stats["saved"] += 1
            else:
                stats["failed"] += 1
        
        log.info(f"📊 Массовая запись: {stats}")
        return stats