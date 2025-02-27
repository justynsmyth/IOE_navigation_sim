import logging

def setup_logger(log_file_path):
    """A logger that writes to both the terminal and a log file."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)

    # Create a file handler
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(logging.INFO)

    # Create a console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(message)s', datefmt='%H:%M:%S')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger