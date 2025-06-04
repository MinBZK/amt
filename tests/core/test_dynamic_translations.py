import pytest
from amt.core.dynamic_translations import ExternalFieldsTranslations
from fastapi import Request
from pytest_mock import MockerFixture


@pytest.mark.asyncio
async def test_translate_with_request(mocker: MockerFixture):
    # given
    mock_request = mocker.Mock(spec=Request)
    mock_translations = mocker.Mock()
    mock_translations.gettext.return_value = "Translated Role"
    mocker.patch("amt.core.dynamic_translations.get_current_translation", return_value=mock_translations)

    # when
    result = ExternalFieldsTranslations.translate("Organization Maintainer", mock_request)

    # then
    assert result == "Translated Role"
    mock_translations.gettext.assert_called_once_with("Organization Maintainer")


@pytest.mark.asyncio
async def test_translate_without_request():
    # given
    key = "Organization Maintainer"

    # when/then
    with pytest.raises(ValueError, match="Request is required to translate external fields"):
        ExternalFieldsTranslations.translate(key, None)


@pytest.mark.asyncio
async def test_translate_key_not_in_translations(mocker: MockerFixture):
    # given
    mock_request = mocker.Mock(spec=Request)
    mock_translations = mocker.Mock()
    mocker.patch("amt.core.dynamic_translations.get_current_translation", return_value=mock_translations)

    # when
    result = ExternalFieldsTranslations.translate("Unknown Key", mock_request)

    # then
    assert result == "Unknown Key"
    mock_translations.gettext.assert_not_called()
