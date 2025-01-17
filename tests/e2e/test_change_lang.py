import pytest
from playwright.sync_api import Cookie, Page, expect


@pytest.mark.slow
def test_e2e_change_language(page_no_login: Page):
    page = page_no_login

    def get_lang_cookie(page: Page) -> Cookie | None:
        for cookie in page.context.cookies():
            if "name" in cookie and cookie["name"] == "lang":
                return cookie
        return None

    page.goto("/")

    # Upon opening make sure no cookie is set.
    lang_cookie = get_lang_cookie(page)
    assert lang_cookie is None

    page.click("#langselect-nl")
    expect(page.locator("#langselect-en")).to_be_visible()
    lang_cookie = get_lang_cookie(page)
    assert lang_cookie is not None
    assert "value" in lang_cookie
    assert lang_cookie["value"] == "nl"

    page.click("#langselect-en")
    expect(page.locator("#langselect-nl")).to_be_visible()
    lang_cookie = get_lang_cookie(page)
    assert lang_cookie is not None
    assert "value" in lang_cookie
    assert lang_cookie["value"] == "en"
