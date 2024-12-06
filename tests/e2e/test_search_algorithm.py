import pytest
from playwright.sync_api import Page, expect


@pytest.mark.slow
def test_e2e_search_algorithms(page: Page) -> None:
    page.goto("/algorithms/?limit=100")

    algorithm_links = page.locator("#search-results-table tr").count() - 1

    assert 90 <= algorithm_links <= 101

    page.locator("#algorithm-search-input").fill("10")

    with page.expect_response(
        "/algorithms/?skip=0&search=10&add-filter-lifecycle=&add-filter-risk-group=&display_type=",
        timeout=3000,
    ) as response_info:
        expect(page.get_by_text("Algorithm 10", exact=True)).to_be_visible()
        expect(page.get_by_text("Algorithm 100", exact=True)).to_be_visible()

    response = response_info.value
    assert response.status == 200


@pytest.mark.slow
def test_e2e_search_scroll_algorithms(page: Page) -> None:
    page.goto("/algorithms/?limit=100")

    algorithm_links = page.locator("#search-results-table tr").count() - 1

    assert 90 <= algorithm_links <= 101

    page.locator("#algorithm-search-input").fill("Algorithm")

    with page.expect_request(
        "/algorithms/?skip=0&search=Algorithm&add-filter-lifecycle=&add-filter-risk-group=&display_type=",
        timeout=3000,
    ) as _:
        algorithm_links = page.locator("#search-results-table tr").count() - 1
        expect(page.get_by_text("Algorithm 100", exact=True)).to_be_visible()
        assert 90 <= algorithm_links <= 101


@pytest.mark.slow
def test_e2e_search_algorithms_with_group_by_lifecycle_view(page: Page) -> None:
    page.goto("/algorithms/?limit=100")

    algorithm_links = page.locator("#search-results-table tr").count() - 1

    assert 90 <= algorithm_links <= 101

    page.locator("#algorithm-search-input").fill("Algorithm")
    page.locator("#display_type").select_option("LIFECYCLE")

    with page.expect_request(
        "/algorithms/?skip=0&search=Algorithm&add-filter-lifecycle=&add-filter-risk-group=&display_type=LIFECYCLE",
        timeout=3000,
    ) as _:
        expect(page.get_by_title("Organizational Responsibilities", exact=True)).to_be_visible()
        expect(page.get_by_text("121 results for 'Algorithm'", exact=True)).to_be_visible()


@pytest.mark.slow
def test_e2e_search_algorithms_with_group_by_lifecycle_view_and_search(page: Page) -> None:
    page.goto("/algorithms/?limit=100")

    algorithm_links = page.locator("#search-results-table tr").count() - 1

    assert 90 <= algorithm_links <= 101

    page.locator("#algorithm-search-input").fill("10")
    page.locator("#display_type").select_option("LIFECYCLE")

    with page.expect_request(
        "/algorithms/?skip=0&search=10&add-filter-lifecycle=&add-filter-risk-group=&display_type=LIFECYCLE",
        timeout=3000,
    ) as _:
        expect(page.get_by_title("Organizational Responsibilities", exact=True)).to_be_visible()
        expect(page.get_by_text("12 results for '10'", exact=True)).to_be_visible()
