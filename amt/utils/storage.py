import logging
from pathlib import Path
from typing import Any

from amt.services.storage import StorageFactory

logger = logging.getLogger(__name__)


def get_include_content(base_dir: Path, system_card: str, include_name: str, search_key: str) -> dict[str, Any] | None:
    """
    Searches for `search_key` in the `include_name` fields in the system card. `include_name` can be `assessments` or
    `models`.
    Example:
        base_dir = /
        system_card = "system_card.yaml"
        include_name = "assessments"
        search_key = "IAMA"

        Suppose the system_card.yaml contains the following:
            ```
            assessments:
                - name: "IAMA"
                  ...
                - name: "AIIA"
            ```
        Then the function would return the contents of the assessment with name equal to "IAMA".

    """
    storage_service = StorageFactory.init(storage_type="file", location=base_dir, filename=system_card)
    system_card_data: Any = storage_service.read()

    for content in system_card_data[include_name]:
        if search_key.lower() in content["name"].lower():
            return content

    logger.warning("could not fetch contents")
    return None
