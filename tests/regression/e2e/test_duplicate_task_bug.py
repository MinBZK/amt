from time import sleep

from playwright.sync_api import Page, expect
from tests.constants import all_statusses, default_task
from tests.database_test_utils import DatabaseTestUtils


def test_duplicate_task(page: Page, db: DatabaseTestUtils) -> None:
    """
    When a task is dragged while being updated, an error occurred in the browser
    resulting in visual duplicates of the card being dragged.
    This test captured that behaviour.
    """

    all_status = all_statusses()
    db.given([*all_status])
    db.given([default_task(status_id=all_status[0].id)])

    page.goto("/pages/")

    expect(page.locator("#column-1 #card-container-1")).to_be_visible()
    expect(page.locator("#column-3")).to_be_visible()

    page.evaluate('document.getElementById("cardMovedForm").setAttribute("hx-target","#card-content-1")')
    page.evaluate('document.getElementsByName("taskId")[0].value = 1')
    page.evaluate('document.getElementsByName("statusId")[0].value = 2')
    page.evaluate('document.getElementsByName("previousSiblingId")[0].value = -1')
    page.evaluate('document.getElementsByName("nextSiblingId")[0].value = -1')

    page.locator("#card-container-1").hover()
    page.mouse.down()
    page.locator("#column-3").hover()
    page.evaluate('htmx.trigger("#cardMovedForm", "cardmoved")')
    sleep(1)
    page.mouse.up()
    cards = page.locator(".progress_card_container").all()
    assert len(cards) == 1
