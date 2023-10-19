import logging
import os
import yaml

from datetime import datetime
from rich.logging import RichHandler


class Logger:
    """
    A Singleton logger class that allows dynamic log level configuration.
    """

    _instance = None

    def __new__(cls):
        """
        Singleton creation of the Logger instance.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance.config = cls.load_config()
            cls._instance.initialize()
        return cls._instance

    @classmethod
    def load_config(cls):
        """
        Load the logging configuration from 'settings.yaml'.
        Raises:
            Exception: If the 'settings.yaml' file is not found.
        """
        try:
            with open('settings.yaml', 'r') as config_file:
                return yaml.safe_load(config_file)
        except FileNotFoundError:
            raise Exception("The configuration file 'settings.yaml' is not found.")

    def initialize(self):
        """
        Initialize the logger with the configured log level and handlers.
        """
        self.logger = logging.getLogger(self.config.get('logger_name', 'MiroLogger'))
        self.logger.setLevel(logging.getLevelName(self.config.get('log_level', 'INFO')))
        self.setup_handlers()

    def setup_handlers(self):
        """
        Set up logging handlers based on the configuration.
        """
        self.setup_handler('stream', 0)
        self.setup_handler('file', 1)

    def setup_handler(self, handler_type, handler_index):
        """
            Set up a specific logging handler (stream or file) based on the configuration.

            Args:
                handler_type (str): The type of handler ('stream' or 'file').
                handler_index (int): The index of the handler configuration.

            Returns:
                None
        """
        handler_config = self.config.get('handlers', [])[handler_index]
        handler = None

        if handler_type == 'stream':
            handler = RichHandler(markup=True, rich_tracebacks=True, highlighter=None)
        elif handler_type == 'file':
            current_date = datetime.now().strftime("%Y-%m-%d")
            logs_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../logs'))
            log_file_path = os.path.join(logs_dir, f'logs-{current_date}.log')
            handler = logging.FileHandler(log_file_path)

        if handler:
            handler.setLevel(logging.getLevelName(self.config.get('log_level', 'INFO')))
            format_str = handler_config.get('formatter', {}).get('format', '')
            formatter = logging.Formatter(fmt=format_str,
                                          datefmt=handler_config.get('formatter', {}).get('date_format', None))
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

    def set_log_level(self, level):
        """
        Set the log level dynamically during runtime.
        Args:
            level (int): The desired log level (e.g., logging.DEBUG, logging.INFO).
        """
        self.logger.setLevel(level)


# Create the Logger instance and expose the logger object
logger = Logger().logger
