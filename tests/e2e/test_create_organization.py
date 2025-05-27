import pytest
from playwright.sync_api import Page, expect


@pytest.mark.slow
def test_e2e_create_organization(page: Page) -> None:
    page.goto("/organizations/new")

    page.locator("#organizationname").click()
    page.locator("#organizationname").fill("new test organization")
    page.keyboard.press("ArrowLeft")  # we need a key-up event for the slug to fill
    page.locator("#organizationuser_ids-search").click()
    page.locator("#organizationuser_ids-search").fill("test")
    page.locator("li").filter(has_text="Test User").click()
    page.get_by_role("button", name="Add organization").click()

    expect(page.get_by_text("Test User").first).to_be_visible()


@pytest.mark.slow
def test_e2e_create_organization_error(page: Page) -> None:
    page.goto("/organizations/new")

    page.locator("#organizationname").click()
    page.get_by_role("button", name="Add organization").click()

    expect(page.get_by_text("String should have at least 3 characters").first).to_be_visible()
