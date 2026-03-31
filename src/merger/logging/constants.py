import logging

# Custom log levels
UPDATE_LEVEL = 25
logging.addLevelName(UPDATE_LEVEL, "UPDATE")

# Logging colors configuration
LOG_COLORS = {
    "INFO": "bold cyan",
    "ERROR": "bold red",
    "WARNING": "bold yellow",
    "DEBUG": "bold green",
    "CRITICAL": "bold red reverse",
    "UPDATE": "bold yellow"
}
