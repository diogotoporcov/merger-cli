import logging

from rich.logging import RichHandler


class RichColorFormatter(logging.Formatter):
    """
    Custom formatter that adds rich colors to the log level and follows 
    the format: [<TYPE>] <Message>.
    """
    COLORS = {
        "INFO": "bold cyan",
        "ERROR": "bold red",
        "WARNING": "bold yellow",
        "DEBUG": "bold green",
        "CRITICAL": "bold red reverse"
    }

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, "white")
        orig_levelname = record.levelname
        record.levelname = f"[{color}][{orig_levelname}][/{color}]"
        res = super().format(record)
        record.levelname = orig_levelname
        return res


def setup_logger(name: str = "merger", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    for handler in list(logger.handlers):
        logger.removeHandler(handler)

    handler = RichHandler(
        rich_tracebacks=True, 
        show_path=False, 
        show_time=False, 
        show_level=False,
        markup=True
    )
    handler.setFormatter(RichColorFormatter("%(levelname)s %(message)s"))
    logger.addHandler(handler)

    return logger


logger = setup_logger()
