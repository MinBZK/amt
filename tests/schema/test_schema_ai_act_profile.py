import pytest
from amt.schema.ai_act_profile import AiActProfile


def test_ai_act_profile_schema_create_new():
    algorithm_new = AiActProfile(
        type="AI-systeem",
        open_source="open-source",
        risk_group="hoog-risico AI",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichting",
        role="aanbieder",
    )
    assert algorithm_new.type == "AI-systeem"
    assert algorithm_new.open_source == "open-source"
    assert algorithm_new.risk_group == "hoog-risico AI"
    assert algorithm_new.systemic_risk == "systeemrisico"
    assert algorithm_new.transparency_obligations == "transparantieverplichting"
    assert algorithm_new.role == "aanbieder"


def test_ai_act_profile_schema_create_new_no_role():
    algorithm_new = AiActProfile(
        type="AI-systeem",
        open_source="open-source",
        risk_group="hoog-risico AI",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichting",
        role=None,
    )
    assert algorithm_new.type == "AI-systeem"
    assert algorithm_new.open_source == "open-source"
    assert algorithm_new.risk_group == "hoog-risico AI"
    assert algorithm_new.systemic_risk == "systeemrisico"
    assert algorithm_new.transparency_obligations == "transparantieverplichting"
    assert algorithm_new.role is None


def test_ai_act_profile_schema_create_new_empty_role_list():
    algorithm_new = AiActProfile(
        type="AI-systeem",
        open_source="open-source",
        risk_group="hoog-risico AI",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichting",
        role=[],
    )
    assert algorithm_new.type == "AI-systeem"
    assert algorithm_new.open_source == "open-source"
    assert algorithm_new.risk_group == "hoog-risico AI"
    assert algorithm_new.systemic_risk == "systeemrisico"
    assert algorithm_new.transparency_obligations == "transparantieverplichting"
    assert algorithm_new.role is None


def test_ai_act_profile_schema_create_new_double_role():
    algorithm_new = AiActProfile(
        type="AI-systeem",
        open_source="open-source",
        risk_group="hoog-risico AI",
        systemic_risk="systeemrisico",
        transparency_obligations="transparantieverplichting",
        role=["aanbieder", "gebruiksverantwoordelijke"],
    )
    assert algorithm_new.type == "AI-systeem"
    assert algorithm_new.open_source == "open-source"
    assert algorithm_new.risk_group == "hoog-risico AI"
    assert algorithm_new.systemic_risk == "systeemrisico"
    assert algorithm_new.transparency_obligations == "transparantieverplichting"
    assert algorithm_new.role == "aanbieder + gebruiksverantwoordelijke"


def test_ai_act_profile_schema_create_new_too_many_roles():
    with pytest.raises(ValueError, match="There can only be two roles"):
        AiActProfile(
            type="AI-systeem",
            open_source="open-source",
            risk_group="hoog-risico AI",
            systemic_risk="systeemrisico",
            transparency_obligations="transparantieverplichting",
            role=["aanbieder", "gebruiksverantwoordelijke", "I am too much of a role"],
        )
