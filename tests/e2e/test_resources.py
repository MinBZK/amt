import logging

import pytest
from playwright.sync_api import ConsoleMessage, Page, expect

logger = logging.getLogger(__name__)


@pytest.mark.slow
def test_validate_resources_and_javascript_errors(page: Page) -> None:
    error_logs: list[ConsoleMessage] = []
    info_logs: list[ConsoleMessage] = []
    page.on("console", lambda msg: error_logs.append(msg) if msg.type == "error" else None)
    page.on("console", lambda msg: info_logs.append(msg) if msg.type != "error" else None)
    page.goto("/")
    expect(page.locator(".header")).to_be_visible()
    if len(error_logs) > 0:
        for error_log in error_logs:
            logger.error(error_log.text + " : " + error_log.location.get("url"))
    assert len(error_logs) == 0
    if len(info_logs) > 0:
        for info_log in info_logs:
            logger.error(info_log.text)
    assert len(info_logs) == 0
