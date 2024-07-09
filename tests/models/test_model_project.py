from pathlib import Path

import pytest
from amt.models.project import Project
from pydantic import ValidationError


def test_model_basic_project():
    # given
    project = Project(name="Test Project", model_card="Test Card")

    # then
    assert project.name == "Test Project"


def test_validate_model_success(tmp_path: Path):
    file = tmp_path / "test.yaml"
    file.write_text("name: Test Project")
    project = Project.model_validate({"name": "Test Project", "model_card": str(file)})
    assert project.name == "Test Project"


def test_validate_model_card_failure():
    with pytest.raises(ValidationError):
        Project.model_validate({"name": "Test Project", "model_card": "Test Card"})
