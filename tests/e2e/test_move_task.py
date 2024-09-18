import pytest
from playwright.sync_api import Page, expect


@pytest.mark.slow
def test_e2e_move_task_to_column(page: Page) -> None:
    """
    Test moving a task in the browser to another column and verify that after a reload
    it is in the right column.
    :param start_server: the start server fixture
    :return: None
    """

    page.goto("/project/1/tasks")

    card = page.get_by_text("task1")
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

    page.drag_and_drop("#card-container-1", "#column-1", target_position={"x": 50, "y": 50})


@pytest.mark.slow
def test_e2e_move_task_order_in_same_column(page: Page) -> None:
    """
    Test moving a task in the page below another task and verify that after a reload
    it is in the right position in the column.
    :return: None
    """

    page.goto("/project/1/tasks")

    card1 = page.get_by_text("task1")
    card2 = page.get_by_text("task2")
    card3 = page.get_by_text("task3")

    expect(card1).to_be_visible()
    expect(card2).to_be_visible()
    expect(card3).to_be_visible()

    with page.expect_response("/tasks/") as response_info:
        page.drag_and_drop("#card-container-1", "#card-container-3", target_position={"x": 50, "y": 50})

    response = response_info.value
    assert response.status == 200

    page.reload()

    tasks_in_column = page.locator("#column-1").locator(".progress-card-container").all()

    expect(tasks_in_column[0]).to_have_id("card-container-2")
    expect(tasks_in_column[1]).to_have_id("card-container-3")
    expect(tasks_in_column[2]).to_have_id("card-container-1")

    card1.drag_to(target=card2)
