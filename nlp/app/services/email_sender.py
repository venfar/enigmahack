# app/services/email_sender.py

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr, formatdate, make_msgid
from email.header import Header
from typing import Optional, List

class EmailSender:
    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        login: str,
        password: str,
        from_email: Optional[str] = None,
        from_name: Optional[str] = None,
        use_tls: bool = True
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.login = login
        self.password = password
        self.from_email = from_email or login
        self.from_name = from_name or login.split('@')[0]
        self.use_tls = use_tls
    
    def send(
        self,
        to_email: str,
        subject: str,
        text: str,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None
    ) -> bool:
        """Отправка письма с корректными заголовками"""
        try:
            # 1. Создаём сообщение
            msg = MIMEMultipart('alternative')
            
            # 2. КОРРЕКТНЫЕ ЗАГОЛОВКИ
            # From: с правильным кодированием имени
            msg['From'] = formataddr((str(Header(self.from_name, 'utf-8')), self.from_email))
            
            # To: просто email
            msg['To'] = to_email
            
            # Subject: с кодированием кириллицы
            msg['Subject'] = Header(subject, 'utf-8')
            
            # Date: обязательный заголовок
            msg['Date'] = formatdate(localtime=True)
            
            # Message-ID: уникальный идентификатор (требуют многие серверы)
            msg['Message-ID'] = make_msgid(domain=self.from_email.split('@')[1])
            
            # Cc (если есть)
            if cc:
                msg['Cc'] = ', '.join(cc)
            
            # 3. Тело письма
            msg.attach(MIMEText(text, 'plain', 'utf-8'))
            
            # 4. Список получателей для отправки
            recipients = [to_email]
            if cc:
                recipients.extend([c.strip() for c in cc if c.strip()])
            if bcc:
                recipients.extend([b.strip() for b in bcc if b.strip()])
            
            # 5. Отправка
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port, timeout=30) as server:
                if self.use_tls:
                    server.starttls(context=context)
                server.login(self.login, self.password)
                server.sendmail(self.from_email, recipients, msg.as_string())
            
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            print(f"❌ Auth error: {e}")
            return False
        except smtplib.SMTPRecipientsRefused as e:
            print(f"❌ Recipients refused: {e}")
            return False
        except Exception as e:
            print(f"❌ Send error: {e}")
            return False