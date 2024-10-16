import pytest
from playwright.sync_api import Page, expect


@pytest.mark.slow
def test_e2e_search_projects(page: Page) -> None:
    page.goto("/algorithm-systems/")

    project_links = page.locator("#search-results-table tr").count() - 1

    assert 90 <= project_links <= 101

    page.locator("#project-search-input").fill("10")

    with page.expect_response(
        "/algorithm-systems/?skip=0&search=10&add-filter-lifecycle=&add-filter-publication-category=", timeout=3000
    ) as response_info:
        expect(page.get_by_text("Project 10", exact=True)).to_be_visible()
        expect(page.get_by_text("Project 100", exact=True)).to_be_visible()

    response = response_info.value
    assert response.status == 200


@pytest.mark.slow
def test_e2e_search_scroll_projects(page: Page) -> None:
    page.goto("/algorithm-systems/")

    project_links = page.locator("#search-results-table tr").count() - 1

    assert 90 <= project_links <= 101

    page.locator("#project-search-input").fill("Project")

    with page.expect_request(
        "/algorithm-systems/?skip=0&search=Project&add-filter-lifecycle=&add-filter-publication-category=", timeout=3000
    ) as _:
        project_links = page.locator("#search-results-table tr").count() - 1
        expect(page.get_by_text("Project 100", exact=True)).to_be_visible()
        assert 90 <= project_links <= 101
