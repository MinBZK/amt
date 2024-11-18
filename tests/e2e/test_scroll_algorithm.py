import pytest
from playwright.sync_api import Page, expect


@pytest.mark.slow
def test_e2e_scroll_algorithms(page: Page) -> None:
    page.goto("/algorithms/?limit=100")

    algorithm_links = page.locator("#search-results-table tr").count() - 1

    assert algorithm_links == 100

    expect(page.locator('[data-marker="last-element"]')).to_be_visible()

    with page.expect_response("/algorithms/?skip=100&search=", timeout=3000) as response_info:
        page.locator('[data-marker="last-element"]').scroll_into_view_if_needed()

    response = response_info.value
    assert response.status == 200

    algorithm_links = page.locator("#search-results-table tr").count()
    assert algorithm_links > 100
