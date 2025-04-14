import logging
import traceback
from typing import Optional
from datetime import datetime

# ANSI color codes for terminal output
COLORS = {
    'DEBUG': '\033[36m',    # Cyan
    'INFO': '\033[32m',     # Green
    'WARNING': '\033[33m',  # Yellow
    'ERROR': '\033[31m',    # Red
    'CRITICAL': '\033[35m', # Magenta
    'RESET': '\033[0m'      # Reset
}

class ColoredFormatter(logging.Formatter):
    def format(self, record):
        # Add color to the level name
        if record.levelname in COLORS:
            record.levelname = f"{COLORS[record.levelname]}{record.levelname}{COLORS['RESET']}"
        return super().format(record)

class StructuredLogger:
    def __init__(self, class_name: str):
        self.logger = logging.getLogger(class_name)
        self.logger.setLevel(logging.INFO)
        self.class_name = class_name

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create formatter with the specified format
        formatter = ColoredFormatter(
            '%(asctime)s.%(msecs)03d %(levelname)s [%(class)s] - %(message)s %(trace)s',
            datefmt='%Y-%m-%dT%H:%M:%S'
        )
        console_handler.setFormatter(formatter)

        # Add handler to logger
        self.logger.addHandler(console_handler)

    def _log(self, level: int, message: str, exc_info: Optional[Exception] = None) -> None:
        """Internal logging method with common formatting."""
        extra = {
            'class': self.class_name,
            'trace': traceback.format_exc() if exc_info else ''
        }
        self.logger.log(level, message, extra=extra)

    def info(self, message: str) -> None:
        """Log info message."""
        self._log(logging.INFO, message)

    def error(self, message: str, exc: Optional[Exception] = None) -> None:
        """Log error message."""
        self._log(logging.ERROR, message, exc)

    def warning(self, message: str) -> None:
        """Log warning message."""
        self._log(logging.WARNING, message)

    def debug(self, message: str) -> None:
        """Log debug message."""
        self._log(logging.DEBUG, message)

    def exception(self, message: str, exc: Exception) -> None:
        """Log exception with full traceback."""
        self._log(logging.ERROR, message, exc)

def get_logger(class_name: str) -> StructuredLogger:
    """Get a logger instance for the specified class."""
    return StructuredLogger(class_name)
