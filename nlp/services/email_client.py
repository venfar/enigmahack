from typing import List, Optional
from datetime import datetime
from imap_tools import MailBox, MailMessage
from email.header import decode_header
from app.core.config import settings
from app.core.logger import log
from app.schemas.email import EmailMessage

class EmailClient:
    """IMAP клиент для получения писем"""
    
    def __init__(self):
        self.imap_server = settings.imap_server
        self.imap_port = settings.imap_port
        self.email_user = settings.email_user
        self.email_password = settings.email_password
        self.folder = settings.email_folder
    
    def connect(self) -> MailBox:
        """Подключение к ящику"""
        try:
            mailbox = MailBox(self.imap_server, port=self.imap_port, timeout=30)
            mailbox.login(self.email_user, self.email_password)
            mailbox.folder.set(self.folder)
            log.success("Подключение к почте успешно")
            return mailbox
        except Exception as e:
            log.error(f"Ошибка подключения к почте: {e}")
            raise
    
    def fetch_new(self, storage) -> List[EmailMessage]:
        """
        Получение ТОЛЬКО новых (необработанных) писем.
        Принимает storage для проверки ID.
        """
        log.info(f"Проверка почты (необработанные)...")
        messages = []
        
        try:
            with self.connect() as mailbox:
                # Берем все непрочитанные
                for msg in mailbox.fetch(unread=True, limit=50):
                    if storage.is_processed(msg.uid):
                        log.debug(f"Письмо #{msg.uid} уже обработано, пропускаем")
                        mailbox.flag(msg.uid, seen=True)
                        continue
                    
                    email_msg = self._parse_message(msg)
                    messages.append(email_msg)
                    
                    # Помечаем как прочитанное на сервере
                    mailbox.flag(msg.uid, seen=True)
                    log.info(f"   Найдено новое письмо #{msg.uid}: {msg.subject}")
            
            log.success(f"Найдено {len(messages)} новых писем для обработки")
            
        except Exception as e:
            log.error(f"Ошибка получения писем: {e}")
            raise
        
        return messages
    
    def _parse_message(self, msg: MailMessage) -> EmailMessage:
        """Парсинг сообщения в модель"""
        # Тема
        subject, encoding = decode_header(msg.subject)[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding or "utf-8", errors="replace")
        
        # Имя отправителя
        sender_name = None
        if msg.from_:
            name_part = msg.from_.split("<")[0].strip()
            if name_part and name_part != msg.from_:
                sender_name, encoding = decode_header(name_part)[0]
                if isinstance(sender_name, bytes):
                    sender_name = sender_name.decode(encoding or "utf-8", errors="replace")
        
        # Вложения
        attachments = [att.filename for att in msg.attachments]
        
        # Тело
        body = msg.text or msg.html or ""
        
        return EmailMessage(
            id=msg.uid,
            subject=subject,
            sender=msg.from_,
            sender_name=sender_name,
            date=msg.date,
            body=body,
            attachments=attachments,
        )