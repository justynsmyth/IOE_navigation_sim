import logging

# Initialize main logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

current_file_handler = None
current_console_handler = None

def setup_logger(log_file_path):
    """Configures the logger to write to both terminal and a log file."""
    global logger, current_file_handler, current_console_handler

    # Remove existing handlers if they exist
    if current_file_handler:
        logger.removeHandler(current_file_handler)
        current_file_handler.close()
    if current_console_handler:
        logger.removeHandler(current_console_handler)

    # Create and configure file handler
    current_file_handler = logging.FileHandler(log_file_path)
    file_formatter = logging.Formatter(
        fmt='%(asctime)s.%(msecs)03d - %(message)s',
        datefmt='%H:%M:%S'
    )
    current_file_handler.setFormatter(file_formatter)
    current_file_handler.setLevel(logging.INFO)

    if not any(isinstance(h, logging.StreamHandler) for h in logger.handlers):
        current_console_handler = logging.StreamHandler()
        current_console_handler.setFormatter(file_formatter)
        current_console_handler.setLevel(logging.INFO)
        logger.addHandler(current_console_handler)

    logger.addHandler(current_file_handler)

    return logger