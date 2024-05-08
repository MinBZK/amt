import logging

from tad.core.config import settings


def set_default_logging_setup():
    logging.basicConfig(level=settings.LOGGING_LEVEL, style="{", format="{asctime}({levelname},{name}): {message}")
    # todo(berry): load from logging.config.dictConfig
    # todo(berry): create RotatingFileHandler for logging to append to the default stream handler
