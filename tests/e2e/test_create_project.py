from playwright.sync_api import Page, expect

from tests.constants import all_statusses
from tests.database_test_utils import DatabaseTestUtils


def test_e2e_create_project(page: Page, db: DatabaseTestUtils):
    all_status = all_statusses()
    db.given([*all_status])

    page.goto("/projects/new")

    page.fill("#name", "My new project")

    impact_assesment = page.get_by_label("Impact Assessment")

    expect(impact_assesment).not_to_be_checked()

    impact_assesment.check()

    button = page.get_by_role("button", name="Create Project")
    button.click()

    page.wait_for_url("project/1", timeout=1000)

    expect(page.get_by_role("heading", name="My new project")).to_be_visible()


def test_e2e_create_project_with_tasks(page: Page, db: DatabaseTestUtils):
    all_status = all_statusses()
    db.given([*all_status])

    page.goto("/projects/new")

    page.fill("#name", "My new filled project")

    impact_assesment = page.get_by_label("Impact Assessment")

    expect(impact_assesment).not_to_be_checked()

    impact_assesment.check()

    button = page.get_by_role("button", name="Create Project")
    button.click()

    page.wait_for_url("project/1", timeout=1000)

    expect(page.get_by_role("heading", name="My new filled project")).to_be_visible()
    card_1 = page.get_by_text("Licht uw voorstel voor het gebruik/de inzet van een algoritme toe.")
    expect(card_1).to_be_visible()
    card_2 = page.get_by_text("Wat is het doel dat bereikt dient te worden met de inzet van het algoritme?")
    expect(card_2).to_be_visible()


def test_e2e_create_project_invalid(page: Page):
    page.goto("/projects/new")

    button = page.get_by_role("button", name="Create Project")
    button.click()

    expect(page.get_by_role("heading", name="Invalid Request")).to_be_visible()
