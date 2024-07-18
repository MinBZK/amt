from playwright.sync_api import Page, expect

from tests.constants import all_statusses, default_task, default_user
from tests.database_test_utils import DatabaseTestUtils


def test_e2e_move_task_to_column(page: Page, db: DatabaseTestUtils) -> None:
    """
    Test moving a task in the browser to another column and verify that after a reload
    it is in the right column.
    :param start_server: the start server fixture
    :return: None
    """
    all_status = all_statusses()
    db.given([*all_status])
    db.given([default_task(status_id=all_status[0].id)])
    db.given([default_user()])

    page.goto("/pages/")

    card = page.get_by_role("heading", name="Default Task")
    expect(card).to_be_visible()

    expect(page.locator("#column-1")).to_be_visible()
    expect(page.locator("#column-3")).to_be_visible()

    with page.expect_response("/tasks/", timeout=1000) as response_info:
        page.drag_and_drop("#card-container-1", "#column-3", target_position={"x": 50, "y": 50})

    response = response_info.value
    assert response.status == 200

    page.reload()

    card = page.locator("#column-3 > #card-container-1")
    expect(card).to_be_visible()


def test_e2e_move_task_order_in_same_column(page: Page, db: DatabaseTestUtils) -> None:
    """
    Test moving a task in the page below another task and verify that after a reload
    it is in the right position in the column.
    :return: None
    """
    all_status = [*all_statusses()]
    db.given([*all_status])

    task1 = default_task(title="task1", status_id=all_status[0].id)
    task2 = default_task(title="task2", status_id=all_status[0].id)
    task3 = default_task(title="task3", status_id=all_status[0].id)

    db.given([task1, task2, task3])

    page.goto("/pages/")

    card1 = page.locator("#card-container-1")
    card2 = page.get_by_text("task2 My default task")
    card3 = page.get_by_text("task3 My default task")

    expect(card1).to_be_visible()
    expect(card2).to_be_visible()
    expect(card3).to_be_visible()

    with page.expect_response("/tasks/") as response_info:
        card1.drag_to(target=card3)

    response = response_info.value
    assert response.status == 200

    page.reload()

    tasks_in_column = page.locator("#column-1").locator(".progress_card_container").all()

    expect(tasks_in_column[0]).to_have_id("card-container-2")
    expect(tasks_in_column[1]).to_have_id("card-container-3")
    expect(tasks_in_column[2]).to_have_id("card-container-1")
