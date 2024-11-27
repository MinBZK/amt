import pytest
from playwright.sync_api import Page, expect

from tests.conftest import do_e2e_login


@pytest.mark.slow
def test_e2e_create_organization(page: Page) -> None:
    do_e2e_login(page)

    page.goto("/organizations/new")

    page.get_by_placeholder("Name of the organization").click()
    page.get_by_placeholder("Name of the organization").fill("new test organization")
    page.keyboard.press("ArrowLeft")  # we need a key-up event for the slug to fill
    page.get_by_placeholder("Search for a person").click()
    page.get_by_placeholder("Search for a person").fill("test")
    page.locator("li").filter(has_text="Test User").click()
    page.get_by_role("button", name="Add organization").click()

    expect(page.get_by_text("new test organization").first).to_be_visible()


@pytest.mark.slow
def test_e2e_create_organization_error(page: Page) -> None:
    do_e2e_login(page)

    page.goto("/organizations/new")

    page.get_by_placeholder("Name of the organization").click()
    page.get_by_role("button", name="Add organization").click()

    expect(page.get_by_text("String should have at least 3 characters").first).to_be_visible()
