from amt.api.deps import custom_context_processor

from tests.constants import default_fastapi_request


def test_custom_context_processor():
    result = custom_context_processor(default_fastapi_request())
    assert result is not None
    assert result["version"] == "0.1.0"
    assert result["available_translations"] == ["en", "nl"]
    assert result["language"] == "en"
    assert result["translations"] is None
