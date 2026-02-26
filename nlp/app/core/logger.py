import sys
from loguru import logger
from .config import settings

def setup_logger():
    logger.remove()
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True
    )
    logger.add(
        "logs/sentiment_{time:YYYY-MM-DD}.log",
        rotation="500 MB",
        retention="7 days",
        level="DEBUG",
        format="{time} | {level} | {name}:{function}:{line} - {message}"
    )
    return logger

log = setup_logger()