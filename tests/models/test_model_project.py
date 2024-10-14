from amt.models.project import Project
from amt.schema.system_card import SystemCard


def test_model_basic_project():
    # given
    project = Project(name="Test Project")

    # then
    assert project.name == "Test Project"


def test_model_systemcard():
    # given
    system_card = SystemCard(name="Test System Card")

    project = Project(name="Test Project", system_card=system_card)

    # then
    assert project.system_card is not None
    assert project.system_card.name == "Test System Card"


def test_model_systemcard_full():
    # given
    system_card = SystemCard(name="Test System Card", description="Test description", status="active")

    project = Project(name="Test Project")
    project.system_card = system_card

    # then
    assert project.system_card is not None
    assert project.system_card.name == "Test System Card"
    assert project.system_card.description == "Test description"
    assert project.system_card.status == "active"

    # when
    project.system_card.name = "Another name"

    # then
    assert project.system_card.name == "Another name"
    assert project.system_card_json["name"] == "Another name"


def test_model_systemcard_direct():
    # given
    project = Project(name="Test Project")
    project.system_card.name = "Test System Card"

    # then
    assert project.system_card.name == "Test System Card"


def test_model_systemcard_equal():
    # given
    system_card = SystemCard(name="Test System Card", description="Test description", status="active")
    project = Project(name="Test Project", system_card=system_card)

    # then
    assert project.system_card.name == "Test System Card"
    assert project.system_card == system_card
    assert system_card == project.system_card

    # when
    project.system_card.name = "Another name"

    # then
    assert project.system_card != system_card
    assert project.system_card != {}


def test_model_systemcard_from_json():
    # given
    project = Project(name="Test Project")

    # when
    project.system_card_json = {"name": "Test System Card"}

    # then
    assert project.system_card == SystemCard(name="Test System Card")


def test_model_systemcard_none():
    # given
    project = Project(name="Test Project")

    # when
    project.system_card = None

    # then
    assert project.system_card == SystemCard()
