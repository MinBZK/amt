from playwright.sync_api import Page, expect

from tests.constants import all_statusses, default_task
from tests.database_test_utils import DatabaseTestUtils


def test_move_task_to_column(browser: Page, db: DatabaseTestUtils) -> None:
    """
    Test moving a task in the browser to another column and verify that after a reload
    it is in the right column.
    :param start_server: the start server fixture
    :return: None
    """
    all_status = all_statusses()
    db.given([*all_status])
    db.given([default_task(status_id=all_status[0].id)])

    browser.goto("/pages/")

    expect(browser.locator("#column-1 #card-container-1")).to_be_visible()
    expect(browser.locator("#column-3")).to_be_visible()

    # todo (Robbert) action below is performed twice, because once does not work, we need find out why and fix it
    browser.locator("#card-container-1").drag_to(browser.locator("#column-3"))
    browser.locator("#card-container-1").drag_to(browser.locator("#column-3"))

    browser.reload()

    card = browser.locator("#column-3 #card-container-1")
    expect(card).to_have_id("card-container-1")
    expect(card).to_be_visible()


def test_move_task_order_in_same_column(browser: Page, db: DatabaseTestUtils) -> None:
    """
    Test moving a task in the browser below another task and verify that after a reload
    it is in the right position in the column.
    :return: None
    """
    all_status = [*all_statusses()]
    db.given([*all_status])

    task1 = default_task(title="Task 1", status_id=all_status[0].id, sort_order=10)
    task2 = default_task(title="Task 2", status_id=all_status[0].id, sort_order=20)
    task3 = default_task(title="Task 3", status_id=all_status[0].id, sort_order=30)

    db.given([task1, task2, task3])

    browser.goto("/pages/")

    expect(browser.locator("#column-1 #card-container-1")).to_be_visible()
    expect(browser.locator("#column-1")).to_be_visible()

    browser.locator("#card-container-1").hover()
    browser.mouse.down()
    # todo (robbert): find out who browser.mouse.move() is not working, we use a locator now instead
    browser.locator("#card-container-2").hover()
    browser.mouse.up()

    browser.reload()

    tasks_in_column = browser.locator("#column-1").locator(".progress_card_container").all()
    # todo (robbert) this order should be changed if code above works correctly
    expect(tasks_in_column[0]).to_have_id("card-container-2")
    expect(tasks_in_column[1]).to_have_id("card-container-1")
    expect(tasks_in_column[2]).to_have_id("card-container-3")
