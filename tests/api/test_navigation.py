import pytest
from amt.api.navigation import (
    BaseNavigationItem,
    DisplayText,
    Navigation,
    NavigationItem,
    _mark_active_navigation_item,  # pyright: ignore [reportPrivateUsage]
    get_main_menu,
    get_translation,
    resolve_base_navigation_items,
    resolve_navigation_items,
    sort_by_path_length,
)
from amt.core import internationalization
from fastapi import Request

from tests.constants import default_base_navigation_item, default_fastapi_request


def test_base_navigation_item():
    item1 = default_base_navigation_item()
    assert item1.custom_display_text == "Default item"
    assert item1.url == "/default/"
    assert item1.icon == "/icons/default.svg"

    item2 = BaseNavigationItem(custom_display_text="Custom text", url="/test/")
    assert item2.get_display_text(None) == "Custom text"

    item3 = BaseNavigationItem(url="/required")
    assert item3.get_display_text(None) == "[Unknown]"


def test_navigation_enum():
    assert type(Navigation.ALGORITHMS_ROOT) is BaseNavigationItem


def test_navigation_item():
    current_translations = internationalization.get_translation("en")
    base_item1 = BaseNavigationItem(display_text=DisplayText.TASKS, url="/test/", icon="icon/test.svg")
    navigation_item1 = NavigationItem(navigation_item=base_item1, translations=current_translations)
    assert navigation_item1.get_url() == "/test/"

    navigation_item2 = NavigationItem(display_text="My item", url=["/path1", "/path2"])
    assert navigation_item2.get_url() == "/path1"
    assert navigation_item2.display_text == "My item"


def test_get_translation():
    current_translations = internationalization.get_translation("en")
    for display_text in DisplayText:
        translated_text = get_translation(display_text, current_translations)
        assert translated_text != ""

    with pytest.raises(KeyError):
        get_translation("raise key error", current_translations)  # pyright: ignore [reportArgumentType]


def test_sort_by_path_length():
    item1 = NavigationItem(display_text="test", url="/a/bb/ccc/dddd")
    assert sort_by_path_length(item1) == (5, 0, 1, 2, 3, 4)

    item_a = NavigationItem(display_text="test", url="/b/bb/ccc/dddd")
    item_b = NavigationItem(display_text="test", url="/a/bb/ccc")
    item_c = NavigationItem(display_text="test", url="/ccc/dddd")
    item_d = NavigationItem(display_text="test", url="/a/bb/ccc/ddddd")
    item_e = NavigationItem(display_text="test", url="/a/bb/ccc/dddd")
    result = sorted([item_a, item_b, item_c, item_d, item_e], key=sort_by_path_length, reverse=True)
    assert result == [item_d, item_a, item_e, item_b, item_c]


def test_get_sub_menu():
    item1 = BaseNavigationItem(custom_display_text="test 1", url="/a/")
    item2 = BaseNavigationItem(custom_display_text="test 2", url="/a/bb/")
    item3 = BaseNavigationItem(custom_display_text="test 3", url="/a/bb/ccc/{algorithm_id}/")
    item4 = BaseNavigationItem(custom_display_text="test 4", url=["/a/bb/ccc/ddd/", "/a/bb/ccc/dddd/"])
    item5 = BaseNavigationItem(display_text=DisplayText.HOME, url="/home")

    request: Request = default_fastapi_request(url="/a/bb/")
    request.state.path_variables = {"algorithm_id": 1}

    sub_menu = resolve_navigation_items([item1, item2, item3, item4, item5], request)
    # assert right item is active
    assert sub_menu[1].active is True

    # assert path resolving worked
    assert sub_menu[2].get_url() == "/a/bb/ccc/1/"

    # assert display text is correct
    assert sub_menu[3].display_text == "test 4"
    assert sub_menu[4].display_text == "Home"


def test_resolve_base_navigation_items():
    request: Request = default_fastapi_request(url="/a/bb/")
    request.state.path_variables = {"algorithm_id": 1}
    item1 = BaseNavigationItem(custom_display_text="test 1", url="/a/bb/")
    item2 = BaseNavigationItem(custom_display_text="test 2", url="/a/bb/ccc/{algorithm_id}/")
    item3 = BaseNavigationItem(display_text=DisplayText.HOME, url="/a/bb/ccc/{algorithm_id}/")
    resolved_items = resolve_base_navigation_items([item1, item2, item3], request)

    # assert path resolving worked
    assert resolved_items[1].get_url() == "/a/bb/ccc/1/"

    # nothing is active
    assert resolved_items[0].active is False
    assert resolved_items[1].active is False

    assert resolved_items[2].display_text == "Home"


def test_get_main_menu():
    main_menu = get_main_menu(
        default_fastapi_request(url="/algorithm-system/"), internationalization.get_translation("en")
    )

    # assert right item is active
    assert len(main_menu) == 1
    assert main_menu[0].active is True

    # assert display text is correct
    assert main_menu[0].display_text == "Algorithm systems"


def test_mark_active_navigation_item():
    def get_test_items() -> list[NavigationItem]:
        return [
            NavigationItem(display_text="test 1", url="/a/"),
            NavigationItem(display_text="test 2", url="/a/bb"),
            NavigationItem(display_text="test 3", url=["/a/bb/cc/", "a/bb/ccc/"]),
            NavigationItem(display_text="test 4", url="/x/y/"),
        ]

    navigation_items1 = _mark_active_navigation_item(get_test_items(), "/a/")
    assert navigation_items1[0].active is True

    navigation_items2 = _mark_active_navigation_item(get_test_items(), "/a/bb/cc/")
    assert navigation_items2[2].active is True

    navigation_items3 = _mark_active_navigation_item(get_test_items(), "/x/y/")
    assert navigation_items3[3].active is True

    item5 = NavigationItem(display_text="test 5", url="/x/y/")
    navigation_items4 = _mark_active_navigation_item([item5], "/no/match/found")
    assert navigation_items4[0].active is False

    navigation_items5 = _mark_active_navigation_item(get_test_items(), "/a/b", True)
    assert navigation_items5[0].active is False
    assert navigation_items5[1].active is False

    navigation_items5 = _mark_active_navigation_item(get_test_items(), "/a/b", False)
    assert navigation_items5[0].active is True
