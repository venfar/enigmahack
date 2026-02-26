from pydantic_settings import BaseSettings
from pydantic import Field

class Settings(BaseSettings):
    model_name: str = Field(
        "blanchefort/rubert-base-cased-sentiment"
    )
    device: str = Field("cpu")
    max_length: int = Field(512)

    host: str = Field("0.0.0.0")
    port: int = Field(8000)
    log_level: str = Field("INFO")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()