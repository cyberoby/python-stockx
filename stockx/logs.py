import logging
import sys

# Create the logger
logger = logging.getLogger('stockx')


def configure_logging(
    level: int = logging.INFO,
    format: str = '[%(levelname)s] [%(module)s]: %(asctime)s - %(message)s',
    datefmt: str = '%Y-%m-%d %H:%M:%S',
    filename: str | None = None,
    stream: bool = True
) -> None:
    """Configure the stockx logger.
    
    Parameters
    ----------
    level : `int`
        The logging level (default: logging.INFO)
    format : `str`
        The log message format
    datefmt : `str`
        The date format
    filename : `str`, optional
        If provided, enables logging to a file
    stream : `bool`, optional
        If `True` (default), enables console logging
    """
    logger.setLevel(level)
    
    formatter = logging.Formatter(format, datefmt)
    
    # Remove any existing handlers
    for handler in logger.handlers:
        logger.removeHandler(handler)
    
    if filename:
        file_handler = logging.FileHandler(filename)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    if stream:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

# Configure default logging at import time
configure_logging()
