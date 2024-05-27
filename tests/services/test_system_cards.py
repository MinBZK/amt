from tad.services.system_cards import SystemCards
import pytest
from tests.database_test_utils import init_db
from tests.utils.create_mock_system_card import create_minimal_model_card


@pytest.fixture(scope="session", autouse=True)
def mock_tasks_and_system_card():
    init_db(
        [
            {"table": "status", "id": 1, "name": "todo", "sort_order": 1},
            {"table": "status", "id": 2, "name": "doing", "sort_order": 2},
            {"table": "status", "id": 3, "name": "done", "sort_order": 3},
            {
                "table": "task",
                "id": 1,
                "descripion": """Licht uw voorstel voor het gebruik/de inzet van een algoritme toe. Wat is de
                                  aanleiding hiervoor geweest? Voor welk probleem moet het algoritme een oplossing
                                  bieden?""",
                "status_id": 1,
            },
            {
                "table": "task",
                "id": 2,
                "descripion": """Wat is het doel dat bereikt dient te worden met de inzet van het algoritme? Wat is
                                  hierbij het hoofddoel en wat zijn subdoelen?""",
                "status_id": 2,
            },
            {
                "table": "task",
                "id": 3,
                "descripion": """Wat zijn de publieke waarden die de inzet van het algoritme ingeven? Indien meerdere
                                  publieke waarden de inzet van het algoritme ingeven, kan daar een rangschikking in
                                  aangebracht worden?""",
                "status_id": 3,
            },
        ]
    )
    create_minimal_model_card()


def test_system_cards():
    print("am I here?")
    system_cards = SystemCards()
    system_cards.update()
