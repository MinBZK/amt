import datetime
from unittest.mock import Mock

import pytest
from babel.support import Translations
from fastapi import Request
from tad.core.internationalization import (
    format_datetime,
    get_dynamic_field_translations,
    get_requested_language,
    get_supported_translation,
    get_translation,
    supported_translations,
)


def test_get_supported_translations():
    lang = get_supported_translation("en")
    assert lang == "en"


def test_fallback_get_supported_translations(caplog: pytest.LogCaptureFixture):
    lang = get_supported_translation("ar")
    assert lang == "en"
    assert caplog.records[0].message == "Requested translation does not exist: ar, using fallback en"


def test_get_all_dynamic_field_translations() -> None:
    assert len(supported_translations) == 3
    for translation in supported_translations:
        get_dynamic_field_translations(translation)


def test_get_lengths_dynamic_field_translations() -> None:
    yaml_en = get_dynamic_field_translations("en")
    assert len(yaml_en) == 4
    yaml_nl = get_dynamic_field_translations("nl")
    assert len(yaml_nl) == 4
    yaml_fy = get_dynamic_field_translations("fy")
    assert len(yaml_fy) == 6
    assert len(yaml_fy["weekdays"]) == 7
    assert len(yaml_fy["months"]) == 12


def test_warning_get_dynamic_field_translations(caplog: pytest.LogCaptureFixture) -> None:
    yaml_en = get_dynamic_field_translations("en")
    yaml_ar = get_dynamic_field_translations("ar")
    assert caplog.records[0].message == "Requested translation does not exist: ar, using fallback en"
    assert yaml_ar == yaml_en


def test_get_translation(caplog: pytest.LogCaptureFixture):
    translation = get_translation("en")
    assert type(translation) is Translations


def test_warning_get_translation(caplog: pytest.LogCaptureFixture):
    translation = get_translation("ar")
    assert caplog.records[0].message == "Requested translation does not exist: ar, using fallback en"
    assert type(translation) is Translations


def test_format_datetime():
    date = datetime.datetime(2020, 1, 2, 12, 13, 14, 0, None)  # noqa
    assert format_datetime(date, "fy", "full") == "tongersdei, 2 jannewaris 2020 12:13"
    assert format_datetime(date, "fy", "medium") == "tongersdei 02-01-2020 12:13"
    assert format_datetime(date, "en", "full") == "Thursday, 2 January 2020 12:13"
    assert format_datetime(date, "en", "medium") == "Thu 02/01/2020 12:13"
    assert format_datetime(date, "nl", "full") == "donderdag, 2 januari 2020 12:13"
    assert format_datetime(date, "nl", "medium") == "do 02/01/2020 12:13"
    assert format_datetime(date, "en", "other") == "02/01/2020 12:13"
    assert format_datetime(date, "nl", "other") == "02/01/2020 12:13"


def test_get_requested_language():
    request: Request = Mock()
    request.cookies.get.return_value = "nl"
    assert get_requested_language(request) == "nl"


def test_fallback_get_requested_language():
    request: Request = Mock()
    request.cookies = {}
    assert get_requested_language(request) == "en"
