import pytest
from playwright.sync_api import Page, expect


@pytest.mark.slow()
def test_e2e_search_projects(page: Page) -> None:
    page.goto("/projects/")

    project_links = page.locator(".project-list > li").count()

    assert 90 <= project_links <= 101

    page.locator("#project-search-input").fill("10")

    with page.expect_response("/projects/?skip=0&search=10", timeout=3000) as response_info:
        expect(page.get_by_text("Project 10", exact=True)).to_be_visible()
        expect(page.get_by_text("Project 100", exact=True)).to_be_visible()

    response = response_info.value
    assert response.status == 200


@pytest.mark.slow()
def test_e2e_search_scroll_projects(page: Page) -> None:
    page.goto("/projects/")

    project_links = page.locator(".project-list > li").count()

    assert 90 <= project_links <= 101

    page.locator("#project-search-input").fill("Project")

    with page.expect_request("/projects/?skip=0&search=Project", timeout=3000) as _:
        project_links = page.locator(".project-list > li").count()
        expect(page.get_by_text("Project 100", exact=True)).to_be_visible()
        assert 90 <= project_links <= 101
