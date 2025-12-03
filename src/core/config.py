from dotenv import load_dotenv
import os

load_dotenv()


def _as_bool(value: str, default: bool = False) -> bool:
    if value is None:
        return default
    return str(value).strip().lower() in ("1", "true", "yes", "y", "on")

def _as_int_list(value: str, default: str = "60"):
    raw = value or default
    return [int(x.strip()) for x in raw.split(",") if x.strip()]


class Config:
    DB_URL = os.getenv("DATABASE_URL")
    FETCH_INTERVAL = int(os.getenv("FETCH_INTERVAL", "60"))
    SYMBOLS = [s.strip() for s in os.getenv("SYMBOLS", "AAPL").split(",") if s.strip()]
    API_PROVIDER = os.getenv("API_PROVIDER", "yfinance")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
    REQUEST_DELAY = float(os.getenv("REQUEST_DELAY", "0.2"))
    SCHEDULER_INTERVAL_SEC = int(os.getenv("SCHEDULER_INTERVAL_SEC", "20"))
    INGEST_INTERVAL_SEC = int(os.getenv("INGEST_INTERVAL_SEC", "30"))
    ANALYTICS_INTERVAL_SEC = int(os.getenv("ANALYTICS_INTERVAL_SEC", "60"))
    CONTEXT_INTERVAL_SEC = int(os.getenv("CONTEXT_INTERVAL_SEC", "300"))
    SUMMARIZER_INTERVAL_SEC = int(os.getenv("SUMMARIZER_INTERVAL_SEC", "60"))
    ANALYTICS_WINDOWS_SECONDS = _as_int_list(os.getenv("ANALYTICS_WINDOW_SECONDS", "60"))
    ANALYTICS_CONCURRENCY = int(os.getenv("ANALYTICS_CONCURRENCY", "5"))
    ANALYTICS_DEBUG_SYMBOLS = _as_bool(os.getenv("ANALYTICS_DEBUG_SYMBOLS", "false"))
    ENABLE_LOG_COLORS = _as_bool(os.getenv("ENABLE_LOG_COLORS", "false"))
    DEBUG = _as_bool(os.getenv("DEBUG", "false"))
    VOLATILITY_SPIKE_THRESHOLD = float(os.getenv("VOLATILITY_SPIKE_THRESHOLD", "0.1"))
    ABNORMAL_PRICE_CHANGE_THRESHOLD = float(os.getenv("ABNORMAL_PRICE_CHANGE_THRESHOLD", "2.0"))
    # Reasoning / model selection
    SUMMARY_MODEL = os.getenv("SUMMARY_MODEL", "rules")  # rules | local | cloud
    LOCAL_SUMMARY_ENDPOINT = os.getenv("LOCAL_SUMMARY_ENDPOINT")  # http://localhost:11434/api/generate, etc.
    LOCAL_SUMMARY_MODEL = os.getenv("LOCAL_SUMMARY_MODEL", "Qwen/Qwen2.5-14B-Instruct")
    LOCAL_SUMMARY_BACKEND = os.getenv("LOCAL_SUMMARY_BACKEND", "tgi")  # tgi | ollama
    CLOUD_SUMMARY_ENDPOINT = os.getenv("CLOUD_SUMMARY_ENDPOINT")  # e.g., https://api.openai.com/v1/chat/completions
    CLOUD_SUMMARY_API_KEY = os.getenv("CLOUD_SUMMARY_API_KEY")
    CLOUD_SUMMARY_MODEL = os.getenv("CLOUD_SUMMARY_MODEL", "gpt-4o-mini")
    SUMMARY_MAX_TOKENS = int(os.getenv("SUMMARY_MAX_TOKENS", "256"))
    # Context ingestion
    ENABLE_NEWS_HARVEST = _as_bool(os.getenv("ENABLE_NEWS_HARVEST", "true"))
    NEWS_CATEGORY = os.getenv("NEWS_CATEGORY", "general")
    NEWS_LOOKBACK_DAYS = int(os.getenv("NEWS_LOOKBACK_DAYS", "3"))
    ENABLE_COMPANY_HARVEST = _as_bool(os.getenv("ENABLE_COMPANY_HARVEST", "true"))
    ENABLE_FINANCIALS_HARVEST = _as_bool(os.getenv("ENABLE_FINANCIALS_HARVEST", "true"))
    FINANCIALS_LOOKBACK_DAYS = int(os.getenv("FINANCIALS_LOOKBACK_DAYS", "7"))
