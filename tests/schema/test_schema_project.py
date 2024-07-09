from amt.schema.project import ProjectNew


def test_project_schema_create_new():
    project_new = ProjectNew(name="Project Name", instruments=["urn:instrument:1", "urn:instrument:2"])
    assert project_new.name == "Project Name"
    assert project_new.instruments == ["urn:instrument:1", "urn:instrument:2"]


def test_project_schema_create_new_one_instrument():
    project_new = ProjectNew(name="Project Name", instruments="urn:instrument:1")
    assert project_new.name == "Project Name"
    assert project_new.instruments == ["urn:instrument:1"]
