from amt.algoritmeregister.mapper import AlgorithmMapper
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.v10_enum_publication_category import (
    V10EnumPublicationCategory,
)
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.v10_enum_status import V10EnumStatus
from amt.api.lifecycles import Lifecycles
from amt.api.risk_group import RiskGroup
from amt.models import Algorithm
from amt.schema.assessment_card import AssessmentCard, AssessmentContent
from amt.schema.system_card import AiActProfile, Label, LegalBaseItem, Owner, Reference

from tests.constants import default_algorithm, default_organization


def create_test_algorithm_with_organization() -> Algorithm:
    """Create a test algorithm with an attached organization."""
    organization = default_organization()
    algorithm = default_algorithm()
    algorithm.organization = organization
    return algorithm


def test_to_publication_model_basic() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.name == "Default System Card"
    assert result.organization == "Test Organisation"


def test_to_publication_model_with_description() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.description = "A test description for the algorithm"

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.description_short == "A test description for the algorithm"


def test_to_publication_model_truncates_long_description() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.description = "A" * 600

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert len(result.description_short) == 500
    assert result.description_short.endswith("...")


def test_to_publication_model_with_status_ontwikkeling() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.status = "in ontwikkeling"

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.status == V10EnumStatus.IN_ONTWIKKELING


def test_to_publication_model_with_status_development() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.status = "development"

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.status == V10EnumStatus.IN_ONTWIKKELING


def test_to_publication_model_with_status_gebruik() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.status = "in gebruik"

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.status == V10EnumStatus.IN_GEBRUIK


def test_to_publication_model_with_status_production() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.status = "production"

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.status == V10EnumStatus.IN_GEBRUIK


def test_to_publication_model_with_status_buiten_gebruik() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.status = "buiten gebruik"

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.status == V10EnumStatus.BUITEN_GEBRUIK


def test_to_publication_model_with_status_retired() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.status = "retired"

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.status == V10EnumStatus.BUITEN_GEBRUIK


def test_to_publication_model_with_status_in_use() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.status = "in use"

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.status == V10EnumStatus.IN_GEBRUIK


def test_to_publication_model_with_status_decommissioned() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.status = "decommissioned"

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.status == V10EnumStatus.BUITEN_GEBRUIK


def test_to_publication_model_status_from_lifecycle_development() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.status = None
    algorithm.lifecycle = Lifecycles.DEVELOPMENT

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.status == V10EnumStatus.IN_ONTWIKKELING


def test_to_publication_model_status_from_lifecycle_implementation() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.status = None
    algorithm.lifecycle = Lifecycles.IMPLEMENTATION

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.status == V10EnumStatus.IN_GEBRUIK


def test_to_publication_model_status_from_lifecycle_monitoring() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.status = None
    algorithm.lifecycle = Lifecycles.MONITORING_AND_MANAGEMENT

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.status == V10EnumStatus.IN_GEBRUIK


def test_to_publication_model_status_from_lifecycle_phasing_out() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.status = None
    algorithm.lifecycle = Lifecycles.PHASING_OUT

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.status == V10EnumStatus.BUITEN_GEBRUIK


def test_to_publication_model_status_default() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.status = None
    algorithm.lifecycle = None

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.status == V10EnumStatus.IN_ONTWIKKELING


def test_to_publication_model_with_begin_date() -> None:
    # given
    from datetime import date

    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.begin_date = date(2024, 1, 15)

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.begin_date == "2024-01"


def test_to_publication_model_with_owner_email() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.owners = [Owner(email="owner@example.com")]  # pyright: ignore[reportCallIssue]

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.contact_email == "owner@example.com"


def test_to_publication_model_contact_email_fallback() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.owners = []  # type: ignore[assignment]

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.contact_email == "noreply@example.com"


def test_to_publication_model_contact_email_owner_without_email() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.owners = [Owner(name="John Doe")]  # pyright: ignore[reportCallIssue]

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.contact_email == "noreply@example.com"


def test_to_publication_model_high_risk_category() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.ai_act_profile = AiActProfile(risk_group=RiskGroup.HOOG_RISICO_AI.value)

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.publication_category == V10EnumPublicationCategory.HOOG_MINUS_RISICO_AI_MINUS_SYSTEEM


def test_to_publication_model_default_category() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.ai_act_profile = None

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.publication_category == V10EnumPublicationCategory.OVERIGE_ALGORITMES


def test_to_publication_model_non_high_risk_category() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.ai_act_profile = AiActProfile(risk_group=RiskGroup.GEEN_HOOG_RISICO_AI.value)

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.publication_category == V10EnumPublicationCategory.OVERIGE_ALGORITMES


def test_to_publication_model_with_legal_base() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.legal_base = [
        LegalBaseItem(name="Law 1", link=None),
        LegalBaseItem(name="Law 2", link=None),
    ]

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.lawful_basis == "Law 1\nLaw 2"


def test_to_publication_model_with_legal_base_grouping() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.legal_base = [
        LegalBaseItem(name="Law 1", link="https://law1.example.com"),
    ]

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.lawful_basis_grouping is not None
    assert len(result.lawful_basis_grouping) == 1
    assert result.lawful_basis_grouping[0].title == "Law 1"
    assert result.lawful_basis_grouping[0].link == "https://law1.example.com"


def test_to_publication_model_with_assessments() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.assessments = [
        AssessmentCard(name="IAMA"),
        AssessmentCard(name="DPIA"),
    ]

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.impacttoetsen == "IAMA, DPIA"


def test_to_publication_model_with_assessments_grouping() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    assessment = AssessmentCard(name="IAMA")
    assessment.contents = [AssessmentContent(urn="urn:test:assessment")]
    algorithm.system_card.assessments = [assessment]

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.impacttoetsen_grouping is not None
    assert len(result.impacttoetsen_grouping) == 1
    assert result.impacttoetsen_grouping[0].title == "IAMA"
    assert result.impacttoetsen_grouping[0].link == "urn:test:assessment"


def test_to_publication_model_with_url_from_reference() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.references = [
        Reference(link="https://example.com/docs"),
    ]

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.url == "https://example.com/docs"


def test_to_publication_model_with_website_from_upl() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.upl = "https://upl.example.com"

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.website == "https://upl.example.com"


def test_to_publication_model_with_tags() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.labels = [
        Label(name="tag1", value="v1"),
        Label(name="tag2", value="v2"),
    ]

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.tags == "tag1, tag2"


def test_to_publication_model_with_provider() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.external_providers = ["Provider Inc."]

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.provider == "Provider Inc."


def test_to_publication_model_with_publiccode_github() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.references = [
        Reference(link="https://github.com/org/repo"),
    ]

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.publiccode == "https://github.com/org/repo"


def test_to_publication_model_with_publiccode_gitlab() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.references = [
        Reference(link="https://gitlab.com/org/repo"),
    ]

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.publiccode == "https://gitlab.com/org/repo"


def test_to_publication_model_no_publiccode_for_other_repos() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.references = [
        Reference(link="https://bitbucket.org/repo"),
    ]

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.publiccode is None


def test_to_publication_model_with_source_data_grouping() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.references = [
        Reference(name="Data Source 1", link="https://source1.example.com"),
    ]

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.source_data_grouping is not None
    assert len(result.source_data_grouping) == 1
    assert result.source_data_grouping[0].title == "Data Source 1"
    assert result.source_data_grouping[0].link == "https://source1.example.com"


def test_to_publication_model_with_goal() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.goal_and_impact = "Test goal"

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.goal == "Test goal"


def test_to_publication_model_with_empty_goal() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.goal_and_impact = ""

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.goal is None


def test_to_publication_model_with_whitespace_goal() -> None:
    # given
    algorithm = create_test_algorithm_with_organization()
    algorithm.system_card.goal_and_impact = "   "

    # when
    result = AlgorithmMapper.to_publication_model(algorithm, "Test Organisation")

    # then
    assert result.goal is None
