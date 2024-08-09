from amt.models.project import Project


def test_model_basic_project():
    # given
    project = Project(name="Test Project", model_card="Test Card")

    # then
    assert project.name == "Test Project"
