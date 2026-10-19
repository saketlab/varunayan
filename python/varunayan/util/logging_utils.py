import logging
import sys


class Colors:
    """ANSI color codes for terminal output."""

    RESET = "\033[0m"
    RED = "\033[0;31m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[0;33m"
    BLUE = "\033[0;34m"
    PURPLE = "\033[0;35m"
    CYAN = "\033[0;36m"
    WHITE = "\033[0;37m"
    GREEN_BRIGHT = "\033[0;92m"
    RED_BRIGHT = "\033[0;91m"
    YELLOW_BRIGHT = "\033[0;93m"
    BLUE_BRIGHT = "\033[0;94m"
    CYAN_BRIGHT = "\033[0;96m"


class ColorFormatter(logging.Formatter):
    """Custom formatter to add colors to log output."""

    LEVEL_COLORS = {
        logging.DEBUG: Colors.BLUE,
        logging.INFO: Colors.RESET,
        logging.WARNING: Colors.YELLOW_BRIGHT,
        logging.ERROR: Colors.RED_BRIGHT,
        logging.CRITICAL: Colors.RED,
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.LEVEL_COLORS.get(record.levelno, Colors.WHITE)
        message = super().format(record)
        return f"{color}{message}{Colors.RESET}"


def get_logger(name: str = "era5_logger", level: int = logging.INFO) -> logging.Logger:
    """Returns a configured logger with colored output."""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Prevent duplicate handlers if logger is re-imported
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = ColorFormatter("%(message)s")
        handler.setFormatter(formatter)
        handler.setLevel(level)
        logger.addHandler(handler)
        logger.propagate = False  # Don't bubble logs to root logger

    return logger
