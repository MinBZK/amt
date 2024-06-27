from unittest.mock import Mock

from fastapi import Request
from tad.api.deps import custom_context_processor
from tad.core.config import VERSION
from tad.core.internationalization import supported_translations


def test_custom_context_processor():
    request: Request = Mock()
    request.cookies.get.return_value = "nl"
    result = custom_context_processor(request)
    assert list(result.keys()) == ["version", "available_translations", "language", "translations"]
    assert result["version"] == VERSION
    assert result["available_translations"] == list(supported_translations)
    assert result["language"] == "nl"
