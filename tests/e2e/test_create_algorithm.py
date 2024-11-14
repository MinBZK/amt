import pytest
from playwright.sync_api import Page, expect


@pytest.mark.slow
def test_e2e_create_algorithm(page: Page):
    page.goto("/algorithm-systems/new")

    page.fill("#name", "My new algorithm")

    button = page.locator("#lifecycle-DATA_EXPLORATION_AND_PREPARATION")
    button.click()

    impact_assessment = page.get_by_label("AI Impact Assessment (AIIA)")

    expect(impact_assessment).not_to_be_checked()

    impact_assessment.check()

    button = page.locator("#transparency_obligations-transparantieverplichtingen")
    button.click()

    button = page.locator("#open_source-open-source")
    button.click()

    button = page.locator("#systemic_risk-systeemrisico")
    button.click()

    button = page.locator("#button-new-algorithm-create")
    button.click()

    expect(page.get_by_text("My new algorithm").first).to_be_visible()


@pytest.mark.slow
def test_e2e_create_algorithm_invalid(page: Page):
    page.goto("/algorithm-systems/new")

    button = page.locator("#transparency_obligations-transparantieverplichtingen")
    button.click()

    button = page.locator("#open_source-open-source")
    button.click()

    button = page.locator("#systemic_risk-systeemrisico")
    button.click()

    button = page.locator("#button-new-algorithm-create")
    button.click()

    expect(page.get_by_text("name: String should have at")).to_be_visible()


@pytest.mark.slow
def test_e2e_create_algorithm_with_tasks(page: Page):
    page.goto("/algorithm-systems/new")

    page.fill("#name", "My new filled algorithm")

    button = page.locator("#lifecycle-DATA_EXPLORATION_AND_PREPARATION")
    button.click()

    impact_assessment = page.get_by_label("AI Impact Assessment (AIIA)")

    expect(impact_assessment).not_to_be_checked()

    impact_assessment.check()

    button = page.locator("#transparency_obligations-transparantieverplichtingen")
    button.click()

    button = page.locator("#open_source-open-source")
    button.click()

    button = page.locator("#systemic_risk-systeemrisico")
    button.click()

    button = page.locator("#button-new-algorithm-create")
    button.click()

    expect(page.get_by_text("My new filled algorithm").first).to_be_visible()
    card_1 = page.get_by_text("Geef een korte beschrijving van het beoogde AI-systeem")
    expect(card_1).to_be_visible()
    card_2 = page.get_by_text("Waarom is er voor de huidige techniek gekozen?")
    expect(card_2).to_be_visible()
