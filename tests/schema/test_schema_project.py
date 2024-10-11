from amt.schema.project import ProjectNew


def test_project_schema_create_new():
    project_new = ProjectNew(
        name="Project Name",
        lifecycle="DATA_EXPLORATION_AND_PREPARATION",
        instruments=["urn:instrument:1", "urn:instrument:2"],
        type="AI-systeem",
        open_source="open-source",
        publication_category="hoog-risico AI",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichtingen",
        role=["aanbieder", "gebruiksverantwoordelijke"],
    )
    assert project_new.name == "Project Name"
    assert project_new.instruments == ["urn:instrument:1", "urn:instrument:2"]
    assert project_new.type == "AI-systeem"
    assert project_new.open_source == "open-source"
    assert project_new.publication_category == "hoog-risico AI"
    assert project_new.systemic_risk == "systeemrisico"
    assert project_new.transparency_obligations == "transparantieverplichtingen"
    assert project_new.role == ["aanbieder", "gebruiksverantwoordelijke"]


def test_project_schema_create_new_one_instrument():
    project_new = ProjectNew(
        name="Project Name",
        lifecycle="DATA_EXPLORATION_AND_PREPARATION",
        instruments="urn:instrument:1",
        type="AI-systeem",
        open_source="open-source",
        publication_category="hoog-risico AI",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichtingen",
        role="aanbieder",
    )
    assert project_new.name == "Project Name"
    assert project_new.instruments == ["urn:instrument:1"]
    assert project_new.type == "AI-systeem"
    assert project_new.open_source == "open-source"
    assert project_new.publication_category == "hoog-risico AI"
    assert project_new.systemic_risk == "systeemrisico"
    assert project_new.transparency_obligations == "transparantieverplichtingen"
    assert project_new.role == ["aanbieder"]
