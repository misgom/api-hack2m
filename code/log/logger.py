import logging
import json
from datetime import datetime
from typing import Dict, Any
from config.settings import Settings

# Create logger instance at module level
_logger = logging.getLogger("hack2m")
_logger.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(formatter)

# Add handler to logger
_logger.addHandler(console_handler)

class StructuredLogger:
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # Create console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)

        # Create formatter
        formatter = logging.Formatter('%(message)s')
        console_handler.setFormatter(formatter)

        # Add handler to logger
        self.logger.addHandler(console_handler)

    def _format_log(self, level: str, message: str, **kwargs) -> str:
        """Format log message as JSON."""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }
        return json.dumps(log_data)

    def info(self, message: str, **kwargs) -> None:
        """Log info message."""
        self.logger.info(self._format_log("INFO", message, **kwargs))

    def error(self, message: str, **kwargs) -> None:
        """Log error message."""
        self.logger.error(self._format_log("ERROR", message, **kwargs))

    def warning(self, message: str, **kwargs) -> None:
        """Log warning message."""
        self.logger.warning(self._format_log("WARNING", message, **kwargs))

    def debug(self, message: str, **kwargs) -> None:
        """Log debug message."""
        self.logger.debug(self._format_log("DEBUG", message, **kwargs))

def setup_logging() -> None:
    """Setup logging configuration."""
    # Configure root logger
    logging.basicConfig(level=logging.INFO)

    # Log startup message
    _logger.info(json.dumps({
        "timestamp": datetime.now().isoformat(),
        "level": "INFO",
        "message": "Logging system initialized"
    }))

# Create logger instance
logger = StructuredLogger("hack2m")
