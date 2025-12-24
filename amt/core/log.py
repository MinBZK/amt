import copy
import logging
import logging.config
from pathlib import Path
from typing import Any

from amt.core.types import LoggingLevelType

LOGGING_SIZE = 10 * 1024 * 1024
LOGGING_BACKUP_COUNT = 5

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "generic": {
            "()": "logging.Formatter",
            "style": "{",
            "fmt": "{asctime}({levelname},{name}): {message}",
            "datefmt": "[%Y-%m-%d %H:%M:%S %z]",
        }
    },
    "handlers": {
        "console": {"formatter": "generic", "class": "logging.StreamHandler", "stream": "ext://sys.stdout"},
    },
    "loggers": {
        "": {"handlers": ["console"], "level": "DEBUG", "propagate": False},
        "httpcore": {"handlers": ["console"], "level": "ERROR", "propagate": False},
        "aiosqlite": {"handlers": ["console"], "level": "INFO", "propagate": False},
        "jinja_roos_components": {"level": "WARN"},
    },
}


def configure_logging(
    level: LoggingLevelType = "INFO",
    config: dict[str, Any] | None = None,
    log_to_file: bool = False,
    logfile_location: Path | None = None,
) -> None:
    log_config: dict[str, Any] = copy.deepcopy(LOGGING_CONFIG)

    # Add file handler if logging to file is enabled
    if log_to_file:
        # Determine the log file path
        log_file_path = logfile_location / "amt.log" if logfile_location else Path("amt.log")

        log_config["handlers"]["file"] = {
            "formatter": "generic",
            "()": "logging.handlers.RotatingFileHandler",
            "filename": str(log_file_path),
            "maxBytes": LOGGING_SIZE,
            "backupCount": LOGGING_BACKUP_COUNT,
        }
        # Add file handler to all logger configurations
        for logger_config in log_config["loggers"].values():
            if "handlers" in logger_config and isinstance(logger_config["handlers"], list):
                logger_config["handlers"].append("file")

    if config:
        log_config.update(config)

    logging.config.dictConfig(log_config)

    logger = logging.getLogger("amt")

    logger.setLevel(level)
