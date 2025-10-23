"""Logging configuration for EdgeCopy v1"""

import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class Logger:
    """Custom logger with file and console output"""

    def __init__(self, name: str = "EdgeCopy", config: dict = None):
        """
        Initialize logger

        Args:
            name: Logger name
            config: Logging configuration dict
        """
        self.name = name
        self.config = config or {}
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """Setup and configure logger"""
        logger = logging.getLogger(self.name)

        # Get config values
        level = self.config.get('level', 'INFO')
        log_format = self.config.get('format', 'detailed')
        log_to_file = self.config.get('log_to_file', True)
        log_to_console = self.config.get('log_to_console', True)
        log_path = self.config.get('log_path', './logs/')

        # Set level
        logger.setLevel(getattr(logging, level.upper()))

        # Clear existing handlers
        logger.handlers = []

        # Create formatter
        if log_format == 'detailed':
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
        else:
            formatter = logging.Formatter(
                '[%(asctime)s] %(levelname)s: %(message)s',
                datefmt='%H:%M:%S'
            )

        # Console handler
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # File handler
        if log_to_file:
            log_dir = Path(log_path)
            log_dir.mkdir(parents=True, exist_ok=True)

            log_file = log_dir / f"edgecopy_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    def debug(self, message: str):
        """Log debug message"""
        self.logger.debug(message)

    def info(self, message: str):
        """Log info message"""
        self.logger.info(message)

    def warning(self, message: str):
        """Log warning message"""
        self.logger.warning(message)

    def error(self, message: str, exc_info: bool = False):
        """Log error message"""
        self.logger.error(message, exc_info=exc_info)

    def critical(self, message: str, exc_info: bool = True):
        """Log critical message"""
        self.logger.critical(message, exc_info=exc_info)


def get_logger(name: str = "EdgeCopy", config: dict = None) -> Logger:
    """
    Get or create logger instance

    Args:
        name: Logger name
        config: Logging configuration

    Returns:
        Logger instance
    """
    return Logger(name, config)
