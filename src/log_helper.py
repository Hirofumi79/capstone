import logging
from functools import wraps
import time
import sys

def log_timing(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        s = time.time()
        result = f(*args, **kwargs)
        logging.info("{} runtime: {} sec".format(f.__name__,time.time() - s))
        return result
    return wrapper


def setup_logging(filename):
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Create STDERR handler
    handlers = [
        logging.FileHandler(filename=filename),
        logging.StreamHandler(sys.stdout)
    ]

    # Create formatter and add it to the handler
    formatter = logging.Formatter(
        "[%(levelname)-7s] " +
        "[%(module)s:%(lineno)d] " +
        "%(asctime)-15s %(name)-12s " +
        "%(message)s"
    )
    for handler in handlers:
        handler.setFormatter(formatter)

    # Set STDERR handler as the only handler
    logger.handlers = handlers