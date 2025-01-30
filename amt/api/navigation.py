import typing
from dataclasses import dataclass
from enum import Enum
from gettext import NullTranslations
from typing import Any

from fastapi import Request

from amt.core.internationalization import get_current_translation


class DisplayText(Enum):
    """
    To avoid duplication and know which labels can be used in navigation items, this enum contains
    all labels.
    """

    REQUIREMENTS = "requirements"
    INSTRUMENTS = "instruments"
    MODEL = "model"
    DATA = "data"
    ALGORITHM_DETAILS = "algorithm_details"
    INFO = "info"
    HOME = "home"
    ALGORITHMS = "algorithms"
    OVERVIEW = "overview"
    TASKS = "tasks"
    NEW = "new"
    SYSTEMCARD = "systemcard"
    ASSESSMENTCARD = "assessmentcard"
    MODELCARD = "modelcard"
    DETAILS = "details"
    ORGANIZATIONS = "organizations"
    MEMBERS = "members"
    COMPLIANCE = "compliance"


def get_translation(key: DisplayText, translations: NullTranslations) -> str:
    """
    Given the key and translation, returns the translated text.
    :param key: the key
    :param translations: translations dictionary
    :return: the translated text
    """
    _ = translations.gettext
    # translations are determined at runtime, which is why we use the dictionary below
    keys = {
        DisplayText.HOME: _("Home"),
        DisplayText.ALGORITHMS: _("Algorithms"),
        DisplayText.OVERVIEW: _("Overview"),
        DisplayText.TASKS: _("Tasks"),
        DisplayText.NEW: _("New"),
        DisplayText.SYSTEMCARD: _("System card"),
        DisplayText.ASSESSMENTCARD: _("Assessment card"),
        DisplayText.MODELCARD: _("Model card"),
        DisplayText.DETAILS: _("Details"),
        DisplayText.INFO: _("Info"),
        DisplayText.ALGORITHM_DETAILS: _("Algorithm details"),
        DisplayText.REQUIREMENTS: _("Requirements"),
        DisplayText.DATA: _("Data"),
        DisplayText.MODEL: _("Model"),
        DisplayText.INSTRUMENTS: _("Instruments"),
        DisplayText.ORGANIZATIONS: _("Organizations"),
        DisplayText.MEMBERS: _("Members"),
        DisplayText.COMPLIANCE: _("Compliance"),
    }
    return keys[key]


@dataclass
class BaseNavigationItem:
    """
    This class is the base for reusable navigation items that can be used for items like
    the main menu, sub menu or breadcrumbs.

    It takes several parameters:
    display_text: a DisplayText label; can be overriden by custom_display_text
    custom_display_text: the text to display, overrides display_text, no translation possible
    url: the url this item links to, can be a list, if a list is used, the first link is used to create links,
     other links are used for URL matching
    icon: the CSS icon to display, only used where applicable
    """

    url: str | list[str]
    custom_display_text: str | None = None
    display_text: DisplayText | None = None
    icon: str | None = None

    def get_display_text(self, translations: NullTranslations | None = None) -> str:
        if self.custom_display_text is not None:
            return self.custom_display_text
        elif self.display_text is not None and translations is not None:
            return get_translation(self.display_text, translations)
        else:
            return "[Unknown]"


class Navigation:
    ALGORITHMS_ROOT = BaseNavigationItem(
        display_text=DisplayText.ALGORITHMS,
        url=["/algorithms/", "/algorithm/"],
        icon="rvo-icon-publicatie",
    )
    ALGORITHMS_OVERVIEW = BaseNavigationItem(display_text=DisplayText.OVERVIEW, url="/algorithms/")
    ALGORITHM_TASKS = BaseNavigationItem(display_text=DisplayText.TASKS, url="/algorithm/{algorithm_id}/tasks")
    ALGORITHM_DETAILS = BaseNavigationItem(
        display_text=DisplayText.ALGORITHM_DETAILS, url="/algorithm/{algorithm_id}/details"
    )
    ALGORITHM_NEW = BaseNavigationItem(display_text=DisplayText.NEW, url="/algorithms/new")
    ALGORITHM_INFO = BaseNavigationItem(display_text=DisplayText.INFO, url="/algorithm/{algorithm_id}/info")

    ALGORITHM_MODEL_CARD = BaseNavigationItem(
        display_text=DisplayText.MODELCARD,
        url="/algorithm/{algorithm_id}/details/system_card/models/{model_card}",
    )
    ALGORITHM_ASSESSMENT_CARD = BaseNavigationItem(
        display_text=DisplayText.ASSESSMENTCARD,
        url="/algorithm/{algorithm_id}/details/system_card/assessment/{assessment_card}",
    )
    ALGORITHM_COMPLIANCE = BaseNavigationItem(
        display_text=DisplayText.COMPLIANCE, url="/algorithm/{algorithm_id}/compliance"
    )
    ALGORITHM_MEMBERS = BaseNavigationItem(display_text=DisplayText.MEMBERS, url="/algorithm/{algorithm_id}/members")
    ORGANIZATIONS_ROOT = BaseNavigationItem(
        display_text=DisplayText.ORGANIZATIONS, url="/organizations", icon="rvo-icon-man-torso-voor-hoogbouw"
    )
    ORGANIZATIONS_NEW = BaseNavigationItem(display_text=DisplayText.NEW, url="/organizations/new")
    ORGANIZATIONS_OVERVIEW = BaseNavigationItem(display_text=DisplayText.OVERVIEW, url="/organizations/")
    ORGANIZATIONS_INFO = BaseNavigationItem(display_text=DisplayText.INFO, url="/organizations/{organization_slug}")
    ORGANIZATIONS_ALGORITHMS = BaseNavigationItem(
        display_text=DisplayText.ALGORITHMS, url="/organizations/{organization_slug}/algorithms"
    )
    ORGANIZATIONS_MEMBERS = BaseNavigationItem(
        display_text=DisplayText.MEMBERS, url="/organizations/{organization_slug}/members"
    )


class NavigationItem:
    """
    This class is the runtime object for navigation items. It should be created per item per request and can
    contain state/context information, like whether it is active or not.

    A NavigationItem can be based on a BaseNavigationItem or custom created. The display_text
    and url can always be overriden.
    """

    display_text: str | None = None
    _url: str | list[str]
    icon: str | None = None
    active: bool = False
    translations: NullTranslations | None = None

    @typing.overload
    def __init__(
        self,
        navigation_item: BaseNavigationItem | None,
        *,
        translations: NullTranslations,
    ) -> None: ...  # pragma: no cover

    @typing.overload
    def __init__(
        self,
        navigation_item: BaseNavigationItem | None,
        display_text: str,
        translations: NullTranslations,
    ) -> None: ...  # pragma: no cover

    @typing.overload
    def __init__(self, *, display_text: str, url: str | list[str]) -> None: ...  # pragma: no cover

    def __init__(
        self,
        navigation_item: BaseNavigationItem | None = None,
        display_text: str | None = None,
        translations: NullTranslations | None = None,
        active: bool = False,
        url: str | list[str] | None = None,
    ) -> None:
        self.active = active
        if navigation_item and translations:
            self.display_text = navigation_item.get_display_text(translations)
            self.icon = navigation_item.icon
            self._url = navigation_item.url
        if display_text is not None:
            self.display_text = display_text
        if url is not None:
            self._url = url

    def get_url(self) -> str:
        if isinstance(self._url, list):
            return self._url[0]
        else:
            return self._url


def sort_by_path_length(navigation_item: NavigationItem) -> tuple[int, Any]:
    parts = navigation_item.get_url().split("/")
    return len(parts), *[len(part) for part in parts]


def resolve_base_navigation_items(
    base_navigation_items: list[BaseNavigationItem], request: Request
) -> list[NavigationItem]:
    """
    Resolves a list of BaseNavigationItems and returns a list of NavigationItems
    :param base_navigation_items: the items to resolve
    :param request: the current request
    :return: a list of resolved NavigationItems
    """
    translations = get_current_translation(request)
    navigation_items: list[NavigationItem] = []

    for base_menu_item in base_navigation_items:
        navigation_items.append(NavigationItem(navigation_item=base_menu_item, translations=translations))

    # resolve urls first, replacing placeholders with actual values
    path_variables: dict[str, typing.Any] = (
        request.state.path_variables if hasattr(request.state, "path_variables") else {}
    )

    for navigation_item in navigation_items:
        if isinstance(navigation_item._url, list):  # pyright: ignore [reportPrivateUsage]
            for idx, url in enumerate(navigation_item._url):  # pyright: ignore [reportPrivateUsage]
                navigation_item._url[idx] = url.format(**path_variables)  # pyright: ignore [reportPrivateUsage]
        else:
            navigation_item._url = navigation_item._url.format(**path_variables)  # pyright: ignore [reportPrivateUsage]

    return navigation_items


def resolve_navigation_items(
    base_sub_menu_items: list[BaseNavigationItem], request: Request, exact_match: bool = True
) -> list[NavigationItem]:
    """
    Resolves the list of BaseNavigationItems and returns a list of NavigationItems. Also
    marks the current active item based on the request URL.
    :param base_sub_menu_items: the items to resolve
    :param request: the current request
    :return: a list of NavigationItems
    """
    sub_menu_items = resolve_base_navigation_items(base_sub_menu_items, request)
    return _mark_active_navigation_item(sub_menu_items, request.url.path, exact_match)


def get_main_menu(request: Request, translations: NullTranslations) -> list[NavigationItem]:
    # main menu items are the same for all pages
    main_menu_items = [
        NavigationItem(Navigation.ALGORITHMS_ROOT, translations=translations),
        NavigationItem(Navigation.ORGANIZATIONS_ROOT, translations=translations),
    ]

    return _mark_active_navigation_item(main_menu_items, request.url.path)


def _url_match(
    menu_item: NavigationItem, url_to_check: str, current_url: str, exact_match: bool
) -> NavigationItem | None:
    if exact_match:
        if current_url == url_to_check:
            menu_item.active = True
            return menu_item
    elif current_url.startswith(url_to_check):
        menu_item.active = True
        return menu_item
    return None


def _mark_active_navigation_item(
    menu_items: list[NavigationItem], current_url: str, exact_match: bool = False
) -> list[NavigationItem]:
    """
    Given the current url, the best matching navigation item in the list based on its url is marked active
    :param menu_items: the menu items
    :param current_url: the current url
    :return: the menu_items
    """

    for menu_item in sorted(menu_items, key=sort_by_path_length, reverse=True):
        if isinstance(menu_item._url, list):  # pyright: ignore [reportPrivateUsage]
            for url in menu_item._url:  # pyright: ignore [reportPrivateUsage]
                if _url_match(menu_item, url, current_url, exact_match) is not None:
                    return menu_items
        else:
            if _url_match(menu_item, menu_item._url, current_url, exact_match) is not None:  # pyright: ignore [reportPrivateUsage]
                return menu_items

    return menu_items
