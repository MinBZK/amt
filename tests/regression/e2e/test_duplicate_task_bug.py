from time import sleep

import pytest
from playwright.sync_api import Page, expect


@pytest.mark.slow
def test_e2e_duplicate_task(page: Page) -> None:
    """
    When a task is dragged while being updated, an error occurred in the browser
    resulting in visual duplicates of the card being dragged.
    This test captured that behaviour.
    """

    page.goto("/project/1/details/tasks")
    cards_begin = page.locator(".progress-card-container").all()

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
    sleep(0.5)
    page.mouse.up()
    cards = page.locator(".progress-card-container").all()
    assert len(cards) == len(cards_begin)
    sleep(0.5)
    page.drag_and_drop("#card-container-1", "#column-1", target_position={"x": 50, "y": 50})
