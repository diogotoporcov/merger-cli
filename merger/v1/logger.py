import logging
import sys


def setup_logger(name: str = "merger", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    else:
        for handler in logger.handlers:
            handler.setLevel(level)

    return logger


logger = setup_logger()
