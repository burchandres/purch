import logging

logging.basicConfig(level=logging.INFO)


def get_logger(name: str):
    logger = logging.getLogger(name)
    return logger
