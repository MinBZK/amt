import pytest
from playwright.sync_api import Page, expect


@pytest.mark.slow
def test_e2e_create_algorithm(page: Page) -> None:
    page.goto("/algorithms/new")

    page.fill("#name", "My new algorithm")

    button = page.locator("#lifecycle-DATA_EXPLORATION_AND_PREPARATION")
    button.click()

    page.locator("#algorithmorganization_id").select_option("default organization")

    page.locator("#role-aanbieder").check()
    page.locator("#type").select_option("AI-systeem voor algemene doeleinden")
    page.locator("#risk_group").select_option("verboden AI")
    page.locator("#transparency_obligations").select_option("geen transparantieverplichting")
    page.locator("#systemic_risk").select_option("geen systeemrisico")
    page.locator("#open_source").select_option("geen open-source")
    page.locator("#conformity_assessment_body").select_option("niet van toepassing")
    page.locator("#conformity_assessment_body").select_option("beoordeling door derde partij")

    with page.expect_response(
        lambda response: "/algorithms/new" in response.url and response.request.method == "POST", timeout=90000
    ) as _:
        button = page.locator("#button-new-algorithm-create")
        button.click()

    expect(page.get_by_text("My new algorithm").first).to_be_visible()


@pytest.mark.slow
def test_e2e_create_algorithm_invalid(page: Page):
    page.goto("/algorithms/new")

    page.locator("#transparency_obligations").select_option("geen transparantieverplichting")

    page.locator("#open_source").select_option("geen open-source")

    page.locator("#systemic_risk").select_option("geen systeemrisico")

    with page.expect_response(
        lambda response: "/algorithms/new" in response.url and response.request.method == "POST", timeout=90000
    ) as _:
        button = page.locator("#button-new-algorithm-create")
        button.click()

    expect(page.get_by_text("String should have at").first).to_be_visible()
