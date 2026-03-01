# app/services/email_sender.py

import smtplib
import ssl
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate, make_msgid
from email.header import Header
from typing import Optional, List

from app.core.config import settings
from app.core.logger import log


class EmailSender:
    """Отправка email с поддержкой SSL/TLS и обработкой самоподписанных сертификатов"""
    
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        login: str,
        password: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        use_tls: bool = True,
        ssl_verify: bool = True,
        ssl_ca_cert: Optional[str] = None
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.login = login
        self.password = password
        self.from_email = from_email or login
        self.from_name = from_name or login.split('@')[0]
        self.use_tls = use_tls
        
        # Настройки SSL
        self.ssl_verify = ssl_verify  # Проверка сертификата (True = строгая проверка)
        self.ssl_ca_cert = ssl_ca_cert  # Путь к CA-сертификату (опционально)
    
    def _create_ssl_context(self) -> ssl.SSLContext:
        """Создание SSL-контекста с учётом настроек проверки"""
        context = ssl.create_default_context()
        
        if not self.ssl_verify:
            # ⚠️ Отключаем проверку только для доверенных внутренних серверов!
            log.warning("⚠️ SSL-проверка отключена (ssl_verify=False)")
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        elif self.ssl_ca_cert and os.path.exists(self.ssl_ca_cert):
            # 🔐 Используем доверенный CA-сертификат
            log.info(f"🔐 Используем CA-сертификат: {self.ssl_ca_cert}")
            context.load_verify_locations(cafile=self.ssl_ca_cert)
        # else: используем стандартные системные сертификаты (по умолчанию)
        
        return context
    
    def send(
        self,
        to_email: str,
        subject: str,
        text: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        html: Optional[str] = None
    ) -> bool:
        """
        Отправка email с корректными заголовками и SSL-обработкой
        
        Returns:
            bool: True если отправлено успешно
        """
        try:
            # 1. Создаём сообщение
            msg = MIMEMultipart('alternative')
            
            # 2. КОРРЕКТНЫЕ ЗАГОЛОВКИ (RFC-compliant)
            msg['From'] = formataddr((str(Header(self.from_name, 'utf-8')), self.from_email))
            msg['To'] = to_email
            msg['Subject'] = Header(subject, 'utf-8')
            msg['Date'] = formatdate(localtime=True)
            msg['Message-ID'] = make_msgid(domain=self.from_email.split('@')[1])
            
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # 3. Тело письма: plain + HTML версии
            msg.attach(MIMEText(text, 'plain', 'utf-8'))
            if html:
                msg.attach(MIMEText(html, 'html', 'utf-8'))
            
            # 4. Список получателей
            recipients = [to_email]
            if cc:
                recipients.extend([c.strip() for c in cc if c.strip()])
            if bcc:
                recipients.extend([b.strip() for b in bcc if b.strip()])
            
            # 5. SSL-контекст и отправка
            ssl_context = self._create_ssl_context()
            
            log.debug(f"Отправка: {self.smtp_host}:{self.smtp_port} → {to_email}")
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                if self.use_tls:
                    server.starttls(context=ssl_context)
                    log.debug("TLS установлен")
                
                server.login(self.login, self.password)
                log.debug("Авторизация успешна")
                
                server.sendmail(self.from_email, recipients, msg.as_string())
                log.debug("Письмо отправлено")
            
            log.success(f"Письмо отправлено: {to_email} | Тема: {subject[:50]}...")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            log.error(f"Ошибка аутентификации SMTP: {e}")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            log.error(f"Получатель отклонён: {e}")
            return False
        except ssl.SSLError as e:
            log.error(f"SSL ошибка: {e}")
            if "self-signed" in str(e).lower():
                log.warning("Подсказка: установите ssl_verify=False или укажите ssl_ca_cert")
            return False
        except Exception as e:
            log.error(f"Ошибка отправки: {type(e).__name__}: {e}", exc_info=True)
            return False