"""
Logging configuration for FlavourCraft
"""
import logging
import sys
import os
from pythonjsonlogger import jsonlogger


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter for structured logging"""
    
    def add_fields(self, log_record, record, message_dict):
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)
        log_record['level'] = record.levelname
        log_record['logger'] = record.name
        log_record['timestamp'] = self.formatTime(record, self.datefmt)


def setup_logger(name: str, level: str = None) -> logging.Logger:
    """
    Configure and return a logger instance
    
    Args:
        name: Logger name (usually __name__)
        level: Optional log level override
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Read credentials directly from environment variables
    environment = os.getenv('ENVIRONMENT', 'development')
    log_level = level or os.getenv('LOG_LEVEL', 'INFO')
    
    # Set level
    logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    logger.handlers = []
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    
    # Use JSON formatter for production, simple formatter for development
    if environment == "production":
        formatter = CustomJsonFormatter(
            '%(timestamp)s %(level)s %(name)s %(message)s'
        )
    else:
        # Colored output for development
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get or create a logger instance
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        Logger instance
    """
    return setup_logger(name)


# Create a default logger for the application
app_logger = get_logger("flavourcraft")