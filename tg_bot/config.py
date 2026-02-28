import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 30))
API_URL = os.getenv("API_URL", "http://0.0.0.0:8000/api/v1/tickets")
STATE_FILE = os.getenv("STATE_FILE", "data/sent_ids.json")