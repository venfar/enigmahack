import imaplib
import email
from email.header import decode_header
from datetime import datetime
import json
import os
import asyncio
import re

from app.core.config import settings
from app.core.logger import log
from app.models.sentiment_model import SentimentAnalyzer
from app.models.classifier_model import Classifier
from app.models.summarizer_model import SummarizerModel
from app.services.parser import Parser
from app.models.response_generator import ResponseGenerator
from app.services.email_sender import EmailSender


class EmailWorker:    
    def __init__(self):
        self.imap_server = settings.imap_server
        self.imap_port = settings.imap_port
        self.email_user = settings.email_user
        self.email_password = settings.email_password
        self.folder = settings.email_folder

        self.smtp_server = settings.smtp_server
        self.smtp_port = settings.smtp_port
        
        self.processed_file = settings.processed_file
        self.processed_ids = self._load_processed_ids()
        
        log.info("Инициализация моделей...")
        self.sentiment = SentimentAnalyzer()
        self.classifier = Classifier()
        self.summarizer = SummarizerModel()
        self.parser = Parser()
        self.response_generator = ResponseGenerator()
        log.success("Все модели загружены")

        self.sender = EmailSender(
            smtp_host=self.smtp_server,
            smtp_port=self.smtp_port,
            login=settings.email_user,
            password=self.email_password,
            from_name="Техподдержка ЭРИС"
        )   
    
    def _load_processed_ids(self) -> set:
        """Загрузка ID обработанных писем"""
        if os.path.exists(self.processed_file):
            try:
                with open(self.processed_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    log.info(f"Загружено {len(data)} ID обработанных писем")
                    return set(data)
            except Exception as e:
                log.warning(f"Ошибка загрузки: {e}")
                return set()
        log.info("Файл обработанных писем не найден")
        return set()
    
    def _save_processed_ids(self):
        """Сохранение ID обработанных писем"""
        try:
            with open(self.processed_file, 'w', encoding='utf-8') as f:
                json.dump(list(self.processed_ids), f, ensure_ascii=False, indent=2)
        except Exception as e:
            log.error(f"Ошибка сохранения: {e}")
    
    def connect(self) -> imaplib.IMAP4_SSL:
        """Подключение к почте"""
        log.info(f"Подключение к {self.imap_server}:{self.imap_port}...")
        try:
            imap = imaplib.IMAP4_SSL(self.imap_server, self.imap_port, timeout=30)
            imap.login(self.email_user, self.email_password)
            log.success("Авторизация успешна")
            return imap
        except Exception as e:
            log.error(f"Ошибка подключения: {e}")
            raise
    
    def decode_subject(self, subject: str) -> str:
        """Декодирование темы письма"""
        if not subject:
            return ""
        decoded, encoding = decode_header(subject)[0]
        if isinstance(decoded, bytes):
            return decoded.decode(encoding or 'utf-8', errors='replace')
        return decoded
    
    def decode_sender(self, sender: str) -> tuple:
        """Декодирование отправителя (имя, email)"""
        if not sender:
            return "", ""
        
        email_match = re.search(r'<([^>]+)>', sender)
        email_addr = email_match.group(1) if email_match else sender
        
        name_part = sender.split('<')[0].strip()
        if name_part:
            decoded, encoding = decode_header(name_part)[0]
            if isinstance(decoded, bytes):
                name = decoded.decode(encoding or 'utf-8', errors='replace')
            else:
                name = decoded
        else:
            name = ""
        
        return name, email_addr
    
    def get_email_body(self, msg: email.message.Message) -> str:
        """Извлечение тела письма (текст)"""
        body = ""
        
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                
                if "attachment" in content_disposition:
                    continue
                
                if content_type == "text/plain":
                    try:
                        charset = part.get_content_charset() or 'utf-8'
                        payload = part.get_payload(decode=True)
                        if payload:
                            body = payload.decode(charset, errors='replace')
                            break
                    except Exception as e:
                        log.warning(f"Ошибка декодирования части письма: {e}")
                        continue
        else:
            try:
                charset = msg.get_content_charset() or 'utf-8'
                payload = msg.get_payload(decode=True)
                if payload:
                    body = payload.decode(charset, errors='replace')
            except Exception as e:
                log.warning(f"Ошибка декодирования письма: {e}")
                body = ""
        
        return body
    
    def process_email(self, email_id: str, msg: email.message.Message) -> dict:
        """Обработка одного письма через конвейер моделей"""
        
        subject = self.decode_subject(msg['Subject'])
        sender_name, sender_email = self.decode_sender(msg['From'])
        date = msg['Date']
        
        text = self.get_email_body(msg)
        
        if not text:
            log.warning(f"Письмо #{email_id} не содержит текста")
            return None
        
        log.info(f"\n{'='*60}")
        log.info(f"ОБРАБОТКА ПИСЬМА #{email_id}")
        log.info(f"   Тема: {subject}")
        log.info(f"   От: {sender_name} <{sender_email}>")
        log.info(f"   Дата: {date}")
        log.info(f"{'='*60}")
        
        # === КОНВЕЙЕР МОДЕЛЕЙ ===
        
        # 1. Анализ тональности
        log.info("Анализ тональности...")
        sentiment_result = self.sentiment.predict(text)
        log.info(f"   Тональность: {sentiment_result['sentiment']} ({sentiment_result['confidence']:.0%})")

        # 2. Классификация запроса
        log.info("Классификация запроса...")
        classifier_result = self.classifier.predict(text, subject)
        log.info(f"   Категория: {classifier_result['category']} ({classifier_result['confidence']:.0%})")

        # 3. Суть вопроса
        log.info("Формирование сути вопроса...")
        summarizer_result = self.summarizer.summarize(text, subject)
        log.info(f"   Суть: {summarizer_result['summary'][:100]}...")
        
        # 4. Парсинг данных (ФИО, телефоны, модели, номера)
        log.info("Извлечение данных...")
        parser_result = self.parser.parse_all(text, subject, sender_name)
        
        # === ФОРМИРОВАНИЕ ЗАПИСИ ДЛЯ ВЕБ-ТАБЛИЦЫ ===
        record = {
            'email_id': email_id,
            'date': date,
            'text': text,
            'fio': parser_result['fio'] or sender_name,
            'object_name': parser_result['object_name'],
            'phone': parser_result['phones'][0] if parser_result['phones'] else None,
            'email': parser_result['emails'][0] if parser_result['emails'] else sender_email,
            'serial_numbers': parser_result['serial_numbers'],
            'device_type': parser_result['device_types'][0] if parser_result['device_types'] else None,
            'description': summarizer_result['summary'],
            'sentiment': sentiment_result['sentiment'],
            'sentiment_confidence': sentiment_result['confidence'],
            'category': classifier_result['category'],
            'category_confidence': classifier_result['confidence'],
            'processed_at': datetime.now().isoformat(),
        }
        
        log.info(f"   ФИО: {record['fio']}")
        log.info(f"   Объект: {record['object_name']}")
        log.info(f"   Телефон: {record['phone']}")
        log.info(f"   Email: {record['email']}")
        log.info(f"   Приборы: {record['device_type']}")
        log.info(f"   Серийные номера: {record['serial_numbers']}")
        
        self.processed_ids.add(email_id)
        self._save_processed_ids()
        
        log.success(f"Письмо #{email_id} успешно обработано")

        log.info("Генерация ответа...")
        response = self.response_generator.generate(record)
        record['response_body'] = response['body']
        record['response_subject'] = response['subject']
        record['response_method'] = response['method']

        log.info("Отправка письма...")
        success = self.sender.send(
            to_email=record['email'],
            subject=record['response_subject'],
            text=record['response_body'],
        )
        if success:
            log.info("Письмо отправлено")
        else:
            log.error("Ошибка отправки")
        return record
    
    def fetch_and_process(self, limit: int = 10) -> list:
        """Получение и обработка непрочитанных писем"""
        log.info(f"Получение непрочитанных писем (лимит: {limit})...")
        
        imap = self.connect()
        processed_records = []
        
        try:
            imap.select(self.folder)
            log.info(f"Папка: {self.folder}")
            
            status, messages = imap.search(None, 'UNSEEN')
            
            if status != 'OK':
                log.warning("Нет непрочитанных писем")
                return []
            
            email_ids = messages[0].split()[:limit]
            log.info(f"Найдено {len(email_ids)} непрочитанных писем")
            
            for email_id in email_ids:
                try:
                    if email_id.decode() in self.processed_ids:
                        log.debug(f"Письмо #{email_id.decode()} уже обработано")
                        imap.store(email_id, '+FLAGS', '\\Seen')
                        continue
                    
                    status, msg_data = imap.fetch(email_id, '(RFC822)')
                    
                    if status != 'OK':
                        log.warning(f"Не удалось получить письмо #{email_id.decode()}")
                        continue
                    
                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)
                    
                    record = self.process_email(email_id.decode(), msg)
                    
                    if record:
                        processed_records.append(record)
                    
                    imap.store(email_id, '+FLAGS', '\\Seen')
                    
                except Exception as e:
                    log.error(f"Ошибка обработки письма #{email_id.decode()}: {e}")
                    continue
            
            log.success(f"Обработано {len(processed_records)} писем")
            
        finally:
            imap.close()
            imap.logout()
        
        return processed_records
    
    def run(self, poll_interval: int = 60):
        """Основной цикл работы"""
        log.info("ЗАПУСК EMAIL WORKER")
        log.info(f"   Почта: {self.email_user}")
        log.info(f"   Сервер: {self.imap_server}:{self.imap_port}")
        log.info(f"   Интервал опроса: {poll_interval} сек")
        log.info("-" * 60)
        
        while True:
            try:
                records = self.fetch_and_process(limit=10)
                
                if not records:
                    log.debug(f"Нет новых писем, ждем {poll_interval} сек...")
                else:
                    # Сохранение в общее хранилище для API
                    self._save_to_api_storage(records)
                
                for i in range(poll_interval):
                    asyncio.run(asyncio.sleep(1))
                    
            except KeyboardInterrupt:
                log.info("Остановка по команде пользователя")
                break
            except Exception as e:
                log.error(f"Критическая ошибка: {e}")
                asyncio.run(asyncio.sleep(10))
    
    def _save_to_api_storage(self, records: list):
        """Сохранение записей в хранилище для API"""
        storage_file = "data/records.json"
        
        existing = []
        if os.path.exists(storage_file):
            try:
                with open(storage_file, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
            except:
                existing = []
        
        existing.extend(records)
        
        os.makedirs(os.path.dirname(storage_file), exist_ok=True)
        with open(storage_file, 'w', encoding='utf-8') as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
        
        log.success(f"Сохранено {len(records)} записей в API хранилище")


# ============================================================================
# ЗАПУСК
# ============================================================================

if __name__ == "__main__":
    worker = EmailWorker()
    worker.run(poll_interval=settings.poll_interval)