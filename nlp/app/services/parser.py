import re
from typing import List, Dict, Optional, Tuple
from app.core.logger import log

from app.models.base.products import (
    ERIS_PRODUCTS, 
    ALL_PRODUCTS, 
    PRODUCT_SYNONYMS,
    SERIAL_NUMBER_PATTERNS
)


class Parser:
    def __init__(self):
        log.info("Parser инициализирован")
        log.success(f"Загружено {len(ALL_PRODUCTS)} моделей ЭРИС")
    
    def find_device_models(self, text: str, subject: str = "") -> List[Dict]:
        """
        Поиск моделей приборов в тексте
        
        Returns:
            Список найденных моделей с категорией
        """
        if not text:
            return []
        
        combined = (subject + " " + text).upper()
        found_models = []
        
        # Поиск по полному названию
        for model in ALL_PRODUCTS:
            if model.upper() in combined:
                # Определяем категорию
                category = self._get_category(model)
                found_models.append({
                    'model': model,
                    'category': category,
                    'method': 'exact'
                })
                log.debug(f"Найдена модель: {model} ({category})")
        
        # Поиск по синонимам
        for model, synonyms in PRODUCT_SYNONYMS.items():
            for synonym in synonyms:
                if synonym.upper() in combined:
                    if not any(m['model'] == model for m in found_models):
                        category = self._get_category(model)
                        found_models.append({
                            'model': model,
                            'category': category,
                            'method': 'synonym'
                        })
                        log.debug(f"Найдена модель по синониму: {model} ({synonym})")
        
        return found_models
    
    def _get_category(self, model: str) -> str:
        """Определение категории модели"""
        for category, products in ERIS_PRODUCTS.items():
            if model in products:
                return category
        return "other"
    
    def find_serial_numbers(self, text: str) -> List[str]:
        """
        Поиск заводских/серийных номеров в тексте
        
        Returns:
            Список найденных номеров
        """
        if not text:
            return []
        
        found_numbers = []
        
        for pattern in SERIAL_NUMBER_PATTERNS:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                # Очистка номера от лишних символов
                number = re.sub(r'[^0-9a-fA-F]', '', match)
                if number and number not in found_numbers:
                    found_numbers.append(number)
                    log.debug(f"🔍 Найден серийный номер: {number}")
        
        return found_numbers
    
    def find_phone_numbers(self, text: str) -> List[str]:
        """
        Поиск телефонных номеров в тексте
        
        Returns:
            Список найденных телефонов
        """
        if not text:
            return []
        
        # Паттерн для российских телефонов
        phone_pattern = r"""
            (?:\+7|7|8)?      # Код страны
            [\s\-]?           # Разделитель
            (?:\(?\d{3}\)?)   # Код города в скобках или без
            [\s\-]?           # Разделитель
            \d{3}             # Первые 3 цифры
            [\s\-]?           # Разделитель
            \d{2}             # Следующие 2 цифры
            [\s\-]?           # Разделитель
            \d{2}             # Последние 2 цифры
        """
        
        matches = re.findall(phone_pattern, text, re.VERBOSE)
        return [m.strip() for m in matches if m.strip()]
    
    def find_emails(self, text: str) -> List[str]:
        """
        Поиск email адресов в тексте
        
        Returns:
            Список найденных email
        """
        if not text:
            return []
        
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        return re.findall(email_pattern, text)
    
    def find_fio(self, text: str, sender_name: str = "") -> Optional[str]:
        """
        Поиск ФИО в тексте
        
        Returns:
            ФИО если найдено
        """
        # Если есть имя отправителя из заголовка
        if sender_name and len(sender_name) > 5:
            return sender_name
        
        # Поиск в тексте (формат: ФИО: ... или в начале письма)
        fio_pattern = r"""
            (?:ФИО|От[:\s]|Фамилия[:\s])?   # Префикс
            \s*
            ([А-ЯЁ][а-яё]+                  # Фамилия
            \s+[А-ЯЁ][а-яё]+                # Имя
            \s+[А-ЯЁ][а-яё]+)               # Отчество
        """
        
        match = re.search(fio_pattern, text, re.IGNORECASE | re.VERBOSE)
        if match:
            return match.group(1).strip()
        
        return None
    
    def find_object_name(self, text: str) -> Optional[str]:
        """
        Поиск названия организации/объекта
        
        Returns:
            Название организации если найдено
        """
        # Паттерны для организаций
        org_patterns = [
            r'(?:ООО|АО|ЗАО|ПАО|ИП)\s*["«]?([А-ЯЁ][а-яё\-\s]+)["»"]?',
            r'(?:предприятие|объект|организация|компания)[:\s]+([А-ЯЁ][а-яё\-\s]+)',
        ]
        
        for pattern in org_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def parse_all(self, text: str, subject: str = "", sender_name: str = "") -> Dict:
        """
        Полный парсинг письма
        
        Returns:
            Dict со всеми извлеченными данными
        """
        log.info("🔍 Полный парсинг письма...")
        
        devices = self.find_device_models(text, subject)
        serials = self.find_serial_numbers(text)
        phones = self.find_phone_numbers(text)
        emails = self.find_emails(text)
        fio = self.find_fio(text, sender_name)
        object_name = self.find_object_name(text)
        
        result = {
            'devices': devices,
            'device_types': [d['model'] for d in devices],
            'serial_numbers': serials,
            'phones': phones,
            'emails': emails,
            'fio': fio,
            'object_name': object_name,
        }
        
        log.info(f"   Найдено моделей: {len(devices)}")
        log.info(f"   Найдено серийных номеров: {len(serials)}")
        log.info(f"   Найдено телефонов: {len(phones)}")
        log.info(f"   Найдено email: {len(emails)}")
        log.info(f"   ФИО: {fio}")
        log.info(f"   Организация: {object_name}")
        
        return result