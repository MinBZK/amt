import pytest
from playwright.sync_api import Page


@pytest.mark.slow()
def test_e2e_scroll_projects(page: Page) -> None:
    page.goto("/projects/")

    project_links = page.locator(".project-list > li", has_text="default project").count()

    assert 90 <= project_links <= 100

    with page.expect_response("/projects/?skip=100", timeout=3000) as response_info:
        page.get_by_text("More").scroll_into_view_if_needed()

    response = response_info.value
    assert response.status == 200

    project_links = page.locator(".project-list > li", has_text="default project").count()
    assert project_links > 100
