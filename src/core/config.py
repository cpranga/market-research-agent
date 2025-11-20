from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    DB_URL = os.getenv("DATABASE_URL")
    FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "60"))
    SYMBOLS = [s.strip() for s in os.getenv("SYMBOLS", "AAPL").split(",")]
    API_PROVIDER = os.getenv("API_PROVIDER", "yfinance")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
    REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.2"))
    SCHEDULER_INTERVAL_SEC = int(os.getenv("SCHEDULER_INTERVAL_SEC", 2))
    ENABLE_LOG_COLORS = bool(os.getenv("ENABLE_LOG_COLORS", "False"))
    DEBUG = bool(os.getenv("DEBUG", "False"))