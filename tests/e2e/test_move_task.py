from playwright.sync_api import Page, expect

from tests.database_test_utils import DatabaseTestUtils


def test_move_task_to_column(browser: Page, db: DatabaseTestUtils) -> None:
    """
    Test moving a task in the browser to another column and verify that after a reload
    it is in the right column.
    :param start_server: the start server fixture
    :return: None
    """
    db.init(
        [
            {"table": "status", "id": 1},
            {"table": "status", "id": 2},
            {"table": "status", "id": 3},
            {"table": "status", "id": 4},
            {"table": "task", "id": 1, "status_id": 1},
        ]
    )

    browser.goto("/pages/")

    expect(browser.locator("#column-1 #card-1")).to_be_visible()
    expect(browser.locator("#column-3")).to_be_visible()

    # todo (Robbert) action below is performed twice, because once does not work, we need find out why and fix it
    browser.locator("#card-1").drag_to(browser.locator("#column-3"))
    browser.locator("#card-1").drag_to(browser.locator("#column-3"))

    browser.reload()

    card = browser.locator("#column-3 #card-1")
    expect(card).to_have_id("card-1")
    expect(card).to_be_visible()


def test_move_task_order_in_same_column(browser: Page, db: DatabaseTestUtils) -> None:
    """
    Test moving a task in the browser below another task and verify that after a reload
    it is in the right position in the column.
    :return: None
    """
    db.init(
        [
            {"table": "task", "id": 1, "status_id": 1},
            {"table": "task", "id": 2, "status_id": 1},
            {"table": "task", "id": 3, "status_id": 1},
        ]
    )

    browser.goto("/pages/")

    expect(browser.locator("#column-1 #card-1")).to_be_visible()
    expect(browser.locator("#column-1")).to_be_visible()

    # todo (robbert) code below doesn't do what it should do, card is not moved
    task = browser.locator("#card-1")
    task.hover()
    browser.mouse.down()
    browser.mouse.move(0, 50)
    browser.mouse.up()
    # https://playwright.dev/docs/input
    browser.reload()

    tasks_in_column = browser.locator("#column-1").locator(".progress_card_container").all()
    # todo (robbert) this order should be changed if code above works correctly
    expect(tasks_in_column[0]).to_have_id("card-1")
    expect(tasks_in_column[1]).to_have_id("card-2")
    expect(tasks_in_column[2]).to_have_id("card-3")
