import logging
import os

import pytest
from tad.core.config import Settings
from tad.core.log import configure_logging


def test_module_logging_setup(caplog: pytest.LogCaptureFixture):
    configure_logging()

    logger = logging.getLogger("tad")

    message = "This is a test log message"
    logger.debug(message)  # defaults to INFO level so debug is not printed
    logger.info(message)
    logger.warning(message)
    logger.error(message)
    logger.critical(message)

    assert len(caplog.records) == 4
    assert caplog.records[0].message == message


def test_root_logging_setup(caplog: pytest.LogCaptureFixture):
    configure_logging()

    logger = logging.getLogger("")

    message = "This is a test log message"
    logger.debug(message)
    logger.info(message)
    logger.warning(message)  # defaults to warning
    logger.error(message)
    logger.critical(message)

    assert len(caplog.records) == 3
    assert caplog.records[0].message == message


def test_module_main_logging_setup(caplog: pytest.LogCaptureFixture):
    configure_logging()

    logger = logging.getLogger("tad.main")

    message = "This is a test log message"
    logger.debug(message)
    logger.info(message)  # should use module logger level
    logger.warning(message)
    logger.error(message)
    logger.critical(message)

    assert len(caplog.records) == 4
    assert caplog.records[0].message == message


def test_module_main_logging_with_custom_logging_setup(caplog: pytest.LogCaptureFixture):
    configure_logging(level="ERROR")

    logger = logging.getLogger("tad.main")

    message = "This is a test log message"
    logger.debug(message)
    logger.info(message)
    logger.warning(message)
    logger.error(message)
    logger.critical(message)

    assert len(caplog.records) == 2


def test_enviroment_setup(caplog: pytest.LogCaptureFixture):
    os.environ["LOGGING_CONFIG"] = '{"formatters": { "generic": {  "fmt": "{name}: {message}"}}}'

    settings = Settings()  # type: ignore

    configure_logging(config=settings.LOGGING_CONFIG)

    logger = logging.getLogger("tad.main")

    message = "This is a test log message with other formatting"
    logger.debug(message)
    logger.info(message)
    logger.warning(message)
    logger.error(message)
    logger.critical(message)

    assert len(caplog.records) == 4
