import pytest
from playwright.sync_api import expect, sync_playwright

from tests.database_test_utils import init_db


@pytest.mark.usefixtures("_start_server")
def test_move_task_to_column() -> None:
    """
    Test moving a task in the browser to another column and verify that after a reload
    it is in the right column.
    :param start_server: the start server fixture
    :return: None
    """
    init_db(
        [
            {"table": "status", "id": 1},
            {"table": "status", "id": 2},
            {"table": "status", "id": 3},
            {"table": "status", "id": 4},
            {"table": "task", "id": 1, "status_id": 1},
        ]
    )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://127.0.0.1:8000/pages/")

        expect(page.locator("#column-1 #card-1")).to_be_visible()
        expect(page.locator("#column-3")).to_be_visible()

        # todo (Robbert) action below is performed twice, because once does not work, we need find out why and fix it
        page.locator("#card-1").drag_to(page.locator("#column-3"))
        page.locator("#card-1").drag_to(page.locator("#column-3"))

        page.reload()

        card = page.locator("#column-3 #card-1")
        expect(card).to_have_id("card-1")
        expect(card).to_be_visible()

        browser.close()


@pytest.mark.usefixtures("_start_server")
def test_move_task_order_in_same_column() -> None:
    """
    Test moving a task in the browser below another task and verify that after a reload
    it is in the right position in the column.
    :return: None
    """
    init_db(
        [
            {"table": "task", "id": 1, "status_id": 1},
            {"table": "task", "id": 2, "status_id": 1},
            {"table": "task", "id": 3, "status_id": 1},
        ]
    )

    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://127.0.0.1:8000/pages/")

        expect(page.locator("#column-1 #card-1")).to_be_visible()
        expect(page.locator("#column-1")).to_be_visible()

        # todo (robbert) code below doesn't do what it should do, card is not moved
        task = page.locator("#card-1")
        task.hover()
        page.mouse.down()
        page.mouse.move(0, 50)
        page.mouse.up()
        # https://playwright.dev/docs/input
        page.reload()

        tasks_in_column = page.locator("#column-1").locator(".progress_card_container").all()
        # todo (robbert) this order should be changed if code above works correctly
        expect(tasks_in_column[0]).to_have_id("card-1")
        expect(tasks_in_column[1]).to_have_id("card-2")
        expect(tasks_in_column[2]).to_have_id("card-3")

        browser.close()
