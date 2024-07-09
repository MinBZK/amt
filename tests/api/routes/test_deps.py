from unittest.mock import Mock

from amt.api.deps import custom_context_processor
from amt.core.config import VERSION
from amt.core.internationalization import supported_translations
from fastapi import Request


def test_custom_context_processor():
    request: Request = Mock()
    request.cookies.get.return_value = "nl"
    result = custom_context_processor(request)
    assert list(result.keys()) == ["version", "available_translations", "language", "translations"]
    assert result["version"] == VERSION
    assert result["available_translations"] == list(supported_translations)
    assert result["language"] == "nl"
