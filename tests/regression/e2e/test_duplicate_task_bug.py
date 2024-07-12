from time import sleep

from playwright.sync_api import Page, expect
from tests.constants import all_statusses, default_task
from tests.database_test_utils import DatabaseTestUtils


def test_duplicate_task(browser: Page, db: DatabaseTestUtils) -> None:
    """
    When a task is dragged while being updated, an error occurred in the browser
    resulting in visual duplicates of the card being dragged.
    This test captured that behaviour.
    """
    error_logs: list[str] = []
    browser.on("console", lambda msg: error_logs.append(msg.text))

    all_status = all_statusses()
    db.given([*all_status])
    db.given([default_task(status_id=all_status[0].id)])

    browser.goto("/pages/")

    expect(browser.locator("#column-1 #card-1")).to_be_visible()
    expect(browser.locator("#column-3")).to_be_visible()

    browser.evaluate('document.getElementById("cardMovedForm").setAttribute("hx-target","#card-1")')
    browser.evaluate('document.getElementsByName("taskId")[0].value = 1')
    browser.evaluate('document.getElementsByName("statusId")[0].value = 2')
    browser.evaluate('document.getElementsByName("previousSiblingId")[0].value = -1')
    browser.evaluate('document.getElementsByName("nextSiblingId")[0].value = -1')

    browser.locator("#card-1").hover()
    browser.mouse.down()
    browser.locator("#column-3").hover()
    browser.evaluate('htmx.trigger("#cardMovedForm", "cardmoved")')
    sleep(1)
    browser.mouse.up()
    cards = browser.locator(".progress_card_container").all()
    assert len(cards) == 2

    expect(browser.locator(".header_logo_container")).to_be_visible()
