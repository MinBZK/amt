import pytest
from playwright.sync_api import Page, expect

from tests.conftest import do_e2e_login


@pytest.mark.slow
def test_e2e_create_algorithm(page: Page) -> None:
    do_e2e_login(page)

    page.goto("/algorithms/new")

    page.fill("#name", "My new algorithm")

    button = page.locator("#lifecycle-DATA_EXPLORATION_AND_PREPARATION")
    button.click()

    page.locator("#algorithmorganization_id").select_option("default organization")

    impact_assessment = page.get_by_label("AI Impact Assessment (AIIA)")

    expect(impact_assessment).not_to_be_checked()

    impact_assessment.check()

    page.locator("#role-aanbieder").check()
    page.locator("#type").select_option("AI-systeem voor algemene doeleinden")
    page.locator("#risk_group").select_option("verboden AI")
    page.locator("#transparency_obligations").select_option("geen transparantieverplichtingen")
    page.locator("#systemic_risk").select_option("geen systeemrisico")
    page.locator("#open_source").select_option("geen open-source")
    page.locator("#conformity_assessment_body").select_option("niet van toepassing")
    page.locator("#conformity_assessment_body").select_option("beoordeling door derde partij")

    button = page.locator("#button-new-algorithm-create")
    button.click()

    page.wait_for_timeout(10000)
    expect(page.get_by_text("My new algorithm").first).to_be_visible()


@pytest.mark.slow
def test_e2e_create_algorithm_invalid(page: Page):
    do_e2e_login(page)

    page.goto("/algorithms/new")

    page.locator("#transparency_obligations").select_option("geen transparantieverplichtingen")

    page.locator("#open_source").select_option("geen open-source")

    page.locator("#systemic_risk").select_option("geen systeemrisico")

    button = page.locator("#button-new-algorithm-create")
    button.click()

    expect(page.get_by_text("name: String should have at")).to_be_visible()
