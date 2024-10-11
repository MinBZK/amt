from datetime import UTC, datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
from amt.core.internationalization import (
    format_datetime,
    get_dynamic_field_translations,
    get_requested_language,
    get_supported_translation,
    get_translation,
    supported_translations,
    time_ago,
)
from babel.support import Translations
from fastapi import Request
from freezegun import freeze_time


def test_get_supported_translations():
    lang = get_supported_translation("en")
    assert lang == "en"


def test_fallback_get_supported_translations(caplog: pytest.LogCaptureFixture):
    lang = get_supported_translation("ar")
    assert lang == "en"
    assert caplog.records[0].message == "Requested translation does not exist: ar, using fallback en"


def test_get_all_dynamic_field_translations() -> None:
    assert len(supported_translations) == 2
    for translation in supported_translations:
        get_dynamic_field_translations(translation)


def test_get_lengths_dynamic_field_translations() -> None:
    yaml_en = get_dynamic_field_translations("en")
    assert yaml_en is None
    yaml_nl = get_dynamic_field_translations("nl")
    assert yaml_nl is None


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
    date = datetime(2020, 1, 2, 12, 13, 14, 0, tzinfo=UTC)
    assert format_datetime(date, "en", "full") == "Thursday, 2 January 2020 12:13"
    assert format_datetime(date, "en", "medium") == "Thu 02/01/2020 12:13"
    assert format_datetime(date, "nl", "full") == "donderdag, 2 januari 2020 12:13"
    assert format_datetime(date, "nl", "medium") == "do 02/01/2020 12:13"
    assert format_datetime(date, "en", "other") == "02/01/2020 12:13"
    assert format_datetime(date, "nl", "other") == "02/01/2020 12:13"


def test_time_ago():
    cases = [
        (timedelta(seconds=30), "en", "30 seconds"),
        (timedelta(minutes=5), "en", "5 minutes"),
        (timedelta(hours=2), "en", "2 hours"),
        (timedelta(days=1), "en", "1 day"),
        (timedelta(weeks=2), "en", "2 weeks"),
        (timedelta(days=45), "en", "2 months"),
        (timedelta(days=365), "en", "1 year"),
        (timedelta(minutes=5), "nl", "5 minuten"),
        (timedelta(hours=10), "nl", "10 uur"),
    ]
    for delta, locale, expected in cases:
        with freeze_time("2024-11-11 12:00:00"):
            now = datetime.now(tz=timezone.utc)  # noqa: UP017
            past_date = now - delta
            assert time_ago(past_date, locale) == expected


def test_get_requested_language():
    request: Request = Mock()
    request.cookies.get.return_value = "nl"
    request.headers.get.return_value = "nl"
    assert get_requested_language(request) == "nl"


def test_fallback_get_requested_language():
    request: Request = Mock()
    request.headers.get.return_value = "en"
    request.cookies = {}
    assert get_requested_language(request) == "en"
