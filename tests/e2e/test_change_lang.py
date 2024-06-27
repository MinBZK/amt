from playwright.sync_api import Cookie, Page, expect


def test_change_language(browser: Page):
    def get_lang_cookie(browser: Page) -> Cookie | None:
        for cookie in browser.context.cookies():
            if "name" in cookie and cookie["name"] == "lang":
                return cookie
        return None

    browser.goto("/pages/")

    # Upon opening make sure no cookie is set.
    lang_cookie = get_lang_cookie(browser)
    assert lang_cookie is None

    browser.click("#langselect-nl")
    expect(browser.locator("#langselect-nl.selected")).to_be_visible()
    lang_cookie = get_lang_cookie(browser)
    assert lang_cookie is not None
    assert "value" in lang_cookie
    assert lang_cookie["value"] == "nl"

    browser.click("#langselect-fy")
    expect(browser.locator("#langselect-fy.selected")).to_be_visible()
    lang_cookie = get_lang_cookie(browser)
    assert lang_cookie is not None
    assert "value" in lang_cookie
    assert lang_cookie["value"] == "fy"

    browser.click("#langselect-en")
    expect(browser.locator("#langselect-en.selected")).to_be_visible()
    lang_cookie = get_lang_cookie(browser)
    assert lang_cookie is not None
    assert "value" in lang_cookie
    assert lang_cookie["value"] == "en"
