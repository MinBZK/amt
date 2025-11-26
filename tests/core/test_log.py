import logging
import os
from pathlib import Path

import pytest
from amt.core.config import Settings
from amt.core.log import configure_logging


def test_logging_amt_module(caplog: pytest.LogCaptureFixture):
    config = {"loggers": {"amt": {"propagate": True}}}

    configure_logging(config=config)

    logger = logging.getLogger("amt")

    message = "This is a test log message"
    logger.debug(message)  # defaults to INFO level so debug is not printed
    logger.info(message)
    logger.warning(message)
    logger.error(message)
    logger.critical(message)

    assert len(caplog.records) == 4
    assert caplog.records[0].message == message


def test_logging_submodule(caplog: pytest.LogCaptureFixture):
    config = {"loggers": {"amt": {"propagate": True}}}

    configure_logging(config=config)

    logger = logging.getLogger("amt.main")

    message = "This is a test log message"
    logger.debug(message)
    logger.info(message)  # should use module logger level
    logger.warning(message)
    logger.error(message)
    logger.critical(message)

    assert len(caplog.records) == 4
    assert caplog.records[0].message == message


def test_logging_config(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv(
        "LOGGING_CONFIG",
        '{"loggers": { "amt": {  "propagate": "True" }},"formatters": { "generic": {  "fmt": "{name}: {message}"}}}',
    )

    settings = Settings()

    configure_logging(config=settings.LOGGING_CONFIG)

    logger = logging.getLogger("amt")

    message = "This is a test log message with other formatting"
    logger.debug(message)
    logger.info(message)
    logger.warning(message)
    logger.error(message)
    logger.critical(message)

    assert len(caplog.records) == 4


def test_logging_loglevel(caplog: pytest.LogCaptureFixture, monkeypatch: pytest.MonkeyPatch):
    config = {"loggers": {"amt": {"propagate": True}}}

    configure_logging(config=config)

    monkeypatch.setenv("LOGGING_LEVEL", "ERROR")

    settings = Settings()

    configure_logging(config=config, level=settings.LOGGING_LEVEL)

    logger = logging.getLogger("amt.main")

    message = "This is a test log message with different logging level"
    logger.debug(message)
    logger.info(message)
    logger.warning(message)
    logger.error(message)
    logger.critical(message)

    assert len(caplog.records) == 2


def test_logging_without_file(caplog: pytest.LogCaptureFixture, tmp_path: Path):
    config = {"loggers": {"amt": {"propagate": True}}}

    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        configure_logging(config=config, log_to_file=False)

        logger = logging.getLogger("amt")
        message = "Test log message without file"
        logger.info(message)

        assert len(caplog.records) == 1
        assert caplog.records[0].message == message

        log_file = tmp_path / "amt.log"
        assert not log_file.exists()
    finally:
        os.chdir(original_cwd)


def test_logging_with_file(tmp_path: Path):
    original_cwd = os.getcwd()
    os.chdir(tmp_path)

    try:
        configure_logging(log_to_file=True)

        logger = logging.getLogger("amt")
        message = "Test log message with file"
        logger.info(message)

        for handler in logger.handlers:
            handler.flush()

        log_file = tmp_path / "amt.log"
        assert log_file.exists()
        log_content = log_file.read_text()
        assert message in log_content
    finally:
        for handler in logging.root.handlers[:]:
            handler.close()
            logging.root.removeHandler(handler)
        os.chdir(original_cwd)


def test_logging_log_to_file_setting(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LOG_TO_FILE", "true")
    settings = Settings()

    assert settings.LOG_TO_FILE is True

    monkeypatch.setenv("LOG_TO_FILE", "false")
    settings = Settings()

    assert settings.LOG_TO_FILE is False


def test_logging_with_custom_location(tmp_path: Path):
    original_cwd = os.getcwd()
    custom_log_dir = tmp_path / "custom_logs"
    custom_log_dir.mkdir()

    try:
        configure_logging(log_to_file=True, logfile_location=custom_log_dir)

        logger = logging.getLogger("amt")
        message = "Test log message with custom location"
        logger.info(message)

        for handler in logger.handlers:
            handler.flush()

        log_file = custom_log_dir / "amt.log"
        assert log_file.exists()
        log_content = log_file.read_text()
        assert message in log_content
    finally:
        for handler in logging.root.handlers[:]:
            handler.close()
            logging.root.removeHandler(handler)
        os.chdir(original_cwd)


def test_logging_logfile_location_setting(monkeypatch: pytest.MonkeyPatch, tmp_path: Path):
    custom_path = str(tmp_path / "logs")

    monkeypatch.setenv("LOGFILE_LOCATION", custom_path)
    settings = Settings()

    assert Path(custom_path) == settings.LOGFILE_LOCATION
