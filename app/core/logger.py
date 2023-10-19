import os
import logging
import datetime
from rich.logging import RichHandler
from pathlib import Path
from dotenv import load_dotenv

load_dotenv('dev.env')

class ColoredFormatter(logging.Formatter):
    """
    A custom log message formatter that adds color to log levels.
    """
    COLORS = {
        'DEBUG': 'blue',
        'INFO': 'green',
        'WARNING': 'yellow',
        'ERROR': 'white on red',
        'CRITICAL': 'white on red',
    }

    def format(self, record):
        """
        Format a log record with added color based on log level.

        Args:
            record (LogRecord): The log record to format.

        Returns:
            str: The formatted log message with color.
        """
        log_message = super().format(record)
        log_level = record.levelname

        if log_level in self.COLORS:
            return f"[{self.COLORS[log_level]}][/]{log_message}"

        return log_message

class Logger:
    """
    A custom logger configuration that supports rich log output and log file separation.
    """
    def __init__(self):
        """
        Initialize the Logger instance.
        """
        self.logger = logging.getLogger('MiroLogger')
        self.setup_logger()

    def setup_logger(self):
        """
        Set up the logger with the specified log level and handlers.
        """
        log_level = self.get_log_level()
        self.logger.setLevel(log_level)

        self.setup_handlers()

    def get_log_level(self):
        """
        Get the log level from the environment variables or use the default level.

        Returns:
            int: The log level (e.g., logging.DEBUG, logging.INFO).
        """
        level_name = os.environ.get('LOG_LEVEL', 'INFO')
        return getattr(logging, level_name)

    def setup_handlers(self):
        """
        Set up the log handlers for console and file output.
        """
        self.setup_stream_handler()
        self.setup_file_handler()

    def setup_stream_handler(self):
        """
        Set up the stream (console) log handler with rich formatting.
        """
        handler = RichHandler(markup=True, rich_tracebacks=True, highlighter=None)
        handler.setFormatter(ColoredFormatter(fmt='%(asctime)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.addHandler(handler)

    def setup_file_handler(self):
        """
        Set up the file log handler and create a separate log file for errors.
        """
        log_dir = Path(os.environ.get('LOG_DIR', 'logs'))
        log_dir.mkdir(parents=True, exist_ok=True)

        current_date = datetime.datetime.now().strftime('%Y-%m-%d')
        log_file_path = log_dir / f'logs-{current_date}.log'
        error_log_file_path = log_dir / f'logs-{current_date}-ERROR.log'

        handler = logging.FileHandler(log_file_path)
        handler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
                                               datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.addHandler(handler)

        error_handler = logging.FileHandler(error_log_file_path)
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(logging.Formatter(fmt='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s',
                                                     datefmt='%Y-%m-%d %H:%M:%S'))
        self.logger.addHandler(error_handler)

    def set_log_level(self, level):
        """
        Set the log level for the logger.

        Args:
            level (int): The log level to set (e.g., logging.DEBUG, logging.INFO).
        """
        self.logger.setLevel(level)

    def log(self, message, level=logging.INFO):
        """
        Log a message with the specified log level.

        Args:
            message (str): The log message to be recorded.
            level (int, optional): The log level (e.g., logging.DEBUG, logging.INFO). Defaults to logging.INFO.
        """
        log_functions = {
            logging.DEBUG: self.logger.debug,
            logging.INFO: self.logger.info,
            logging.WARNING: self.logger.warning,
            logging.ERROR: self.logger.error,
            logging.CRITICAL: self.logger.critical
        }

        log_function = log_functions.get(level, None)

        if log_function:
            log_function(message)
        else:
            self.logger.warning(f'Invalid log level: {level}. Logging as INFO instead.')
            self.logger.info(message)

logger = Logger().logger
