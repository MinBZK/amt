from amt.schema.algorithm import AlgorithmNew


def test_algorithm_schema_create_new():
    algorithm_new = AlgorithmNew(
        name="Algorithm Name",
        lifecycle="DATA_EXPLORATION_AND_PREPARATION",
        instruments=["urn:instrument:1", "urn:instrument:2"],
        type="AI-systeem",
        open_source="open-source",
        risk_group="hoog-risico AI",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichtingen",
        role=["aanbieder", "gebruiksverantwoordelijke"],
        organization_id=1,
    )
    assert algorithm_new.name == "Algorithm Name"
    assert algorithm_new.instruments == ["urn:instrument:1", "urn:instrument:2"]
    assert algorithm_new.type == "AI-systeem"
    assert algorithm_new.open_source == "open-source"
    assert algorithm_new.risk_group == "hoog-risico AI"
    assert algorithm_new.systemic_risk == "systeemrisico"
    assert algorithm_new.transparency_obligations == "transparantieverplichtingen"
    assert algorithm_new.role == ["aanbieder", "gebruiksverantwoordelijke"]
    assert algorithm_new.organization_id == 1


def test_algorithm_schema_create_new_one_instrument():
    algorithm_new = AlgorithmNew(
        name="Algorithm Name",
        lifecycle="DATA_EXPLORATION_AND_PREPARATION",
        instruments="urn:instrument:1",
        type="AI-systeem",
        open_source="open-source",
        risk_group="hoog-risico AI",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichtingen",
        role="aanbieder",
        organization_id=1,
    )
    assert algorithm_new.name == "Algorithm Name"
    assert algorithm_new.instruments == ["urn:instrument:1"]
    assert algorithm_new.type == "AI-systeem"
    assert algorithm_new.open_source == "open-source"
    assert algorithm_new.risk_group == "hoog-risico AI"
    assert algorithm_new.systemic_risk == "systeemrisico"
    assert algorithm_new.transparency_obligations == "transparantieverplichtingen"
    assert algorithm_new.role == ["aanbieder"]
    assert algorithm_new.organization_id == 1
