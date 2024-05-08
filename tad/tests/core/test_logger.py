import logging

import pytest
from tad.core.logger import set_default_logging_setup


def test_set_default_logging_setup(caplog: pytest.LogCaptureFixture):
    set_default_logging_setup()

    logger = logging.getLogger("tad.main")

    message = "This is a test log message"
    logger.info(message)
    logger.debug(message)

    assert len(caplog.records) == 1
    assert caplog.records[0].message == message
