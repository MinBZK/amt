from playwright.sync_api import Page, expect


def test_validate_deployment(validate_version: str, browser: Page) -> None:
    error_logs: list[str] = []
    info_logs: list[str] = []
    browser.on("console", lambda msg: error_logs.append(msg.text) if msg.type == "error" else None)
    browser.on("console", lambda msg: info_logs.append(msg.text) if msg.type != "error" else None)
    browser.goto("/pages/")
    expect(browser.locator(".header_logo_container")).to_be_visible()
    assert validate_version is not None
    assert len(error_logs) == 0
    assert "TAD loaded successfully" in info_logs
