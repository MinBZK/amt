from playwright.sync_api import Page, expect


def test_e2e_create_project(page: Page):
    page.goto("/projects/new")

    page.fill("#name", "My new project")

    impact_assesment = page.get_by_label("Impact Assessment")

    expect(impact_assesment).not_to_be_checked()

    impact_assesment.check()

    button = page.get_by_role("button", name="Create Project")
    button.click()

    page.wait_for_url("project/1", timeout=1000)

    expect(page.get_by_role("heading", name="My new project")).to_be_visible()


def test_e2e_create_project_invalud(page: Page):
    page.goto("/projects/new")

    button = page.get_by_role("button", name="Create Project")
    button.click()

    expect(page.get_by_role("heading", name="Invalid Request")).to_be_visible()
