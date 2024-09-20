from amt.schema.ai_act_profile import AiActProfile


def test_ai_act_profile_schema_create_new():
    project_new = AiActProfile(
        type="AI-systeem",
        open_source="open-source",
        publication_category="hoog-risico AI",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichtingen",
        role="aanbieder",
    )
    assert project_new.type == "AI-systeem"
    assert project_new.open_source == "open-source"
    assert project_new.publication_category == "hoog-risico AI"
    assert project_new.systemic_risk == "systeemrisico"
    assert project_new.transparency_obligations == "transparantieverplichtingen"
    assert project_new.role == "aanbieder"
