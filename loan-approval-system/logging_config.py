"""
Centralized Logging Configuration
Provides structured logging with JSON format for production environments.
"""
import logging
import logging.handlers
import json
from datetime import datetime
from pathlib import Path

LOG_DIR = Path(__file__).parent.parent / "logs"
LOG_DIR.mkdir(exist_ok=True)

LOG_FORMAT_DEV = '[%(levelname)-8s] [%(asctime)s] [%(name)s] - %(message)s'
LOG_FORMAT_PROD = '%(message)s'  # JSON format handled in JSONFormatter


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON for production."""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "function": record.funcName,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_data)


def get_logger(name: str, level: str = "INFO", use_json: bool = False) -> logging.Logger:
    """
    Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        use_json: If True, output JSON format (for production)

    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(getattr(logging, level))

    # Console handler (development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, level))

    if use_json:
        console_handler.setFormatter(JSONFormatter())
    else:
        console_handler.setFormatter(logging.Formatter(LOG_FORMAT_DEV))

    logger.addHandler(console_handler)

    # File handler (production)
    log_file = LOG_DIR / f"{name.split('.')[-1]}.log"
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5
    )
    file_handler.setLevel(getattr(logging, level))

    if use_json:
        file_handler.setFormatter(JSONFormatter())
    else:
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT_DEV))

    logger.addHandler(file_handler)
    logger.propagate = False

    return logger


def get_structlog(name: str, applicant_id: str = None, **context) -> logging.Logger:
    """
    Get a logger with structured context (applicant_id, etc).
    Wraps standard logger to add context to all messages.

    Args:
        name: Logger name
        applicant_id: Applicant ID for context
        **context: Additional context key-value pairs

    Returns:
        Logger-like object with context
    """
    logger = get_logger(name)
    return StructuredLogger(logger, applicant_id=applicant_id, **context)


class StructuredLogger:
    """Wrapper around logger to add structured context to all messages."""

    def __init__(self, logger: logging.Logger, applicant_id: str = None, **context):
        self.logger = logger
        self.applicant_id = applicant_id
        self.context = context

    def _format_message(self, msg: str) -> str:
        """Add context to message."""
        parts = []
        if self.applicant_id:
            parts.append(f"[{self.applicant_id}]")
        parts.append(msg)
        return " ".join(parts)

    def debug(self, msg: str, **kwargs):
        self.logger.debug(self._format_message(msg), **kwargs)

    def info(self, msg: str, **kwargs):
        self.logger.info(self._format_message(msg), **kwargs)

    def warning(self, msg: str, **kwargs):
        self.logger.warning(self._format_message(msg), **kwargs)

    def error(self, msg: str, **kwargs):
        self.logger.error(self._format_message(msg), **kwargs)

    def critical(self, msg: str, **kwargs):
        self.logger.critical(self._format_message(msg), **kwargs)
