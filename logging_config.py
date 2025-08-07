"""
Logging configuration for UltimaScraperAPI
"""
import logging
import sys
from datetime import datetime

def setup_logging(level=logging.INFO):
    """
    Configure logging for the entire application
    """
    # Create logs directory if it doesn't exist
    import os
    os.makedirs('logs', exist_ok=True)
    
    # Create formatters
    detailed_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    simple_formatter = logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(simple_formatter)
    
    # File handler
    file_handler = logging.FileHandler(
        f'logs/ultima_scraper_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(detailed_formatter)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)
    
    # Configure specific loggers
    loggers_config = {
        'ultima_scraper_api': logging.DEBUG,
        'aiohttp': logging.INFO,
        'urllib3': logging.WARNING,
    }
    
    for logger_name, logger_level in loggers_config.items():
        logger = logging.getLogger(logger_name)
        logger.setLevel(logger_level)
    
    return root_logger


def get_logger(name):
    """Get a logger instance with the given name"""
    return logging.getLogger(name)