import pytest
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


def test_ai_act_profile_schema_create_new_no_role():
    project_new = AiActProfile(
        type="AI-systeem",
        open_source="open-source",
        publication_category="hoog-risico AI",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichtingen",
        role=None,
    )
    assert project_new.type == "AI-systeem"
    assert project_new.open_source == "open-source"
    assert project_new.publication_category == "hoog-risico AI"
    assert project_new.systemic_risk == "systeemrisico"
    assert project_new.transparency_obligations == "transparantieverplichtingen"
    assert project_new.role is None


def test_ai_act_profile_schema_create_new_empty_role_list():
    project_new = AiActProfile(
        type="AI-systeem",
        open_source="open-source",
        publication_category="hoog-risico AI",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichtingen",
        role=[],
    )
    assert project_new.type == "AI-systeem"
    assert project_new.open_source == "open-source"
    assert project_new.publication_category == "hoog-risico AI"
    assert project_new.systemic_risk == "systeemrisico"
    assert project_new.transparency_obligations == "transparantieverplichtingen"
    assert project_new.role is None


def test_ai_act_profile_schema_create_new_double_role():
    project_new = AiActProfile(
        type="AI-systeem",
        open_source="open-source",
        publication_category="hoog-risico AI",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichtingen",
        role=["aanbieder", "gebruiksverantwoordelijke"],
    )
    assert project_new.type == "AI-systeem"
    assert project_new.open_source == "open-source"
    assert project_new.publication_category == "hoog-risico AI"
    assert project_new.systemic_risk == "systeemrisico"
    assert project_new.transparency_obligations == "transparantieverplichtingen"
    assert project_new.role == "aanbieder + gebruiksverantwoordelijke"


def test_ai_act_profile_schema_create_new_too_many_roles():
    with pytest.raises(ValueError, match="There can only be two roles"):
        AiActProfile(
            type="AI-systeem",
            open_source="open-source",
            publication_category="hoog-risico AI",
            systemic_risk="systeemrisico",
            transparency_obligations="transparantieverplichtingen",
            role=["aanbieder", "gebruiksverantwoordelijke", "I am too much of a role"],
        )
