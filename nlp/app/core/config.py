from pydantic_settings import BaseSettings
from pathlib import Path
from pydantic import Field
from typing import Optional

class Settings(BaseSettings):
    # === Почтовые настройки ===
    email_user: str = Field("support@eris.ru")
    email_password: str = Field("your_app_password")
    imap_server: str = Field("imap.yandex.ru")
    imap_port: int = Field(993)
    smtp_server: str = Field("smtp.yandex.ru")
    smtp_port: int = Field(587)
    email_folder: str = Field("INBOX")

    # Настройки SSL для SMTP
    smtp_use_tls: bool = True
    smtp_ssl_verify: bool = True          # False — только для внутренних серверов!
    smtp_ssl_ca_cert: Optional[str] = None  # Путь к CA-сертификату
    
    # Отправитель
    from_email: str = "support@eriskip.ru"
    from_name: str = "Техподдержка ООО «ЭРИС»"

    # === Модели ===
    classifier_name: str = Field("cointegrated/rubert-base-cased-nli-threeway")
    sentiment_name: str = Field("blanchefort/rubert-base-cased-sentiment")
    response_name: str = Field("Qwen/Qwen2.5-0.5B-Instruct")
    #summarization_name: str = Field("cointegrated/rubert-tiny2")
    
    device: str = Field("cpu")
    max_length: int = Field(512)

    # === Сервер ===
    host: str = Field("0.0.0.0")
    port: int = Field(8000)

    # === Логи ===
    log_level: str = Field("INFO")

    records_file: Path = Path(__file__).parent.parent.parent / "data" / "records.json"

    # === Интервалы ===
    poll_interval: int = Field(60)
    processed_file: str = Field("processed_emails.json")

    # === MySQL Database ===
    db_host: str = Field("db")
    db_port: int = Field(3306)
    db_user: str = Field("root")
    db_pass: str = Field("root")
    db_name: str = Field("enigma_db")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()