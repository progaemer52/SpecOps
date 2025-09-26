# logger.py

import os
import logging


class CustomLogger:
    _instance = None

    def __new__(cls, log_dir='logs'):
        if cls._instance is None:
            cls._instance = super(CustomLogger, cls).__new__(cls)
            cls._instance._initialize_logger(log_dir)
        return cls._instance

    def _initialize_logger(self, log_dir='logs'):
        """Initialize the logger with a new sequential log file."""
        # Create logs directory if it doesn't exist
        # log_dir = 'logs'
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

        # Find the next log file number
        existing_logs = [f for f in os.listdir(log_dir) if f.startswith('log') and f.endswith('.log')]
        existing_numbers = []
        for log_file in existing_logs:
            try:
                # Extract number from filenames like 'log34.log'
                num = int(log_file[3:-4])
                existing_numbers.append(num)
            except (ValueError, IndexError):
                continue

        # Get the next log number
        next_log_num = 1
        if existing_numbers:
            next_log_num = max(existing_numbers) + 1

        # Create new log filename
        log_filename = os.path.join(log_dir, f'log{next_log_num}.log')

        # Set up the logger
        self._logger = logging.getLogger('app_logger')
        self._logger.setLevel(logging.DEBUG)

        # Clear any existing handlers
        if self._logger.handlers:
            self._logger.handlers.clear()

        # Create file handler
        file_handler = logging.FileHandler(log_filename)

        # Create console handler
        console_handler = logging.StreamHandler()

        # Create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)

        # Add handlers to logger
        self._logger.addHandler(file_handler)
        self._logger.addHandler(console_handler)

        # Log the initialization
        self._logger.info(f"Logger initialized with log file: {log_filename}")

    # Adding direct logging methods to the class
    def debug(self, message):
        """Log a debug message."""
        self._logger.debug(message)

    def info(self, message):
        """Log an info message."""
        self._logger.info(message)

    def warning(self, message):
        """Log a warning message."""
        self._logger.warning(message)

    def error(self, message):
        """Log an error message."""
        self._logger.error(message)

    def critical(self, message):
        """Log a critical message."""
        self._logger.critical(message)

    def rotate_log(self):
        """Close the current log file and open a new one."""
        self._logger.info("Closing current log file and opening a new one")
        self._initialize_logger(self.log_dir)
