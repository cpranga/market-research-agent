import logging
import sys
from core.config import Config

try:
    import colorlog
    COLORLOG_AVAILABLE = True
except ImportError:
    COLORLOG_AVAILABLE = False


def get_logger():
    """Return a configured logger for the market agent."""

    logger = logging.getLogger("market_agent")

    # Prevent creating duplicate handlers if called multiple times
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)  # Base level; handlers will filter

    # ---- Formatter ----
    format_str = "%(asctime)s | %(levelname)s | %(message)s"
    date_fmt = "%Y-%m-%d %H:%M:%S"

    if COLORLOG_AVAILABLE and Config.ENABLE_LOG_COLORS:
        formatter = colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s | %(levelname)s | %(message)s",
            datefmt=date_fmt,
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "bold_red",
            }
        )
    else:
        formatter = logging.Formatter(format_str, date_fmt)

    # ---- Console handler ----
    console = logging.StreamHandler(sys.stdout)
    console.setLevel(logging.INFO if not Config.DEBUG else logging.DEBUG)
    console.setFormatter(formatter)
    logger.addHandler(console)

    # ---- Optional file handler ----
    if getattr(Config, "LOG_FILE", None):
        file_handler = logging.FileHandler(Config.LOG_FILE)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter(format_str, date_fmt))
        logger.addHandler(file_handler)

    return logger


# Shortcut helpers
logger = get_logger()

def info(message):
    logger.info(message)

def error(message):
    logger.error(message)

def debug(message):
    logger.debug(message)

def warning(message):
    logger.warning(message)

def critical(message):
    logger.critical(message)