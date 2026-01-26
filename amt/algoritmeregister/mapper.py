from typing import Any, cast

from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.algorithm_in import (
    AlgorithmIn,
)
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.v10_enum_lang import (
    V10EnumLang,
)
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.v10_enum_publication_category import (
    V10EnumPublicationCategory,
)
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.v10_enum_standard_version import (
    V10EnumStandardVersion,
)
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.v10_enum_status import (
    V10EnumStatus,
)
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.v10_object_impacttoetsen_grouping import (
    V10ObjectImpacttoetsenGrouping,
)
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.v10_object_lawful_basis_grouping import (
    V10ObjectLawfulBasisGrouping,
)
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.v10_object_source_data_grouping import (
    V10ObjectSourceDataGrouping,
)
from amt.api.lifecycles import Lifecycles
from amt.api.risk_group import RiskGroup
from amt.models.algorithm import Algorithm, AlgorithmSystemCard
from amt.models.organization import Organization


class AlgorithmMapper:
    @staticmethod
    def _empty_to_none(value: str | None) -> str | None:
        """Convert empty strings to None for optional fields."""
        if value is None or (isinstance(value, str) and value.strip() == ""):
            return None
        return value

    @staticmethod
    def to_publication_model(
        algorithm: Algorithm,
        organization_name: str,
        lang: V10EnumLang = V10EnumLang.NLD,
    ) -> AlgorithmIn:
        system_card = algorithm.system_card
        organization: Organization = cast(Organization, algorithm.organization)  # pyright: ignore [reportUnknownMemberType]

        return AlgorithmIn(
            name=AlgorithmMapper._get_name(algorithm),
            description_short=AlgorithmMapper._get_description_short(system_card),
            organization=organization_name,
            category=AlgorithmMapper._get_category(system_card),
            status=AlgorithmMapper._map_status(system_card.status, algorithm.lifecycle),
            begin_date=AlgorithmMapper._format_date(system_card.begin_date),
            end_date=AlgorithmMapper._format_date(system_card.end_date),
            contact_email=AlgorithmMapper._get_contact_email(system_card, organization),
            website=AlgorithmMapper._get_website(system_card, organization),
            publication_category=AlgorithmMapper._map_publication_category(system_card),
            url=AlgorithmMapper._get_url(system_card),
            goal=AlgorithmMapper._empty_to_none(system_card.goal_and_impact),
            proportionality=AlgorithmMapper._empty_to_none(system_card.considerations),
            human_intervention=AlgorithmMapper._empty_to_none(system_card.human_intervention),
            risks=AlgorithmMapper._empty_to_none(system_card.risk_management),
            lawful_basis=AlgorithmMapper._get_lawful_basis_text(system_card),
            lawful_basis_grouping=AlgorithmMapper._get_lawful_basis_grouping(system_card),
            process_index_url=AlgorithmMapper._empty_to_none(system_card.upl),
            impacttoetsen_grouping=AlgorithmMapper._get_impacttoetsen_grouping(system_card),
            impacttoetsen=AlgorithmMapper._get_impacttoetsen_text(system_card),
            source_data=AlgorithmMapper._empty_to_none(system_card.used_data),
            source_data_grouping=AlgorithmMapper._get_source_data_grouping(system_card),
            methods_and_models=AlgorithmMapper._empty_to_none(system_card.technical_design),
            provider=AlgorithmMapper._get_provider(system_card),
            publiccode=AlgorithmMapper._get_publiccode(system_card),
            lang=lang,
            standard_version=V10EnumStandardVersion.ENUM_1_DOT_0,
            source_id=str(algorithm.id) if algorithm.id else None,
            tags=AlgorithmMapper._get_tags(system_card),
            lars="string",
            publication_dt="string",
        )

    @staticmethod
    def _get_name(algorithm: Algorithm) -> str:
        return algorithm.system_card.name or algorithm.name or "Unnamed Algorithm"

    @staticmethod
    def _get_description_short(system_card: AlgorithmSystemCard) -> str:
        description = system_card.description or ""
        max_length = 500
        if len(description) > max_length:
            return description[: max_length - 3] + "..."
        return description or "No description available"

    @staticmethod
    def _get_organization(organization: Organization) -> str:
        return organization.name

    @staticmethod
    def _get_category(system_card: AlgorithmSystemCard) -> list[Any] | None:
        return None

    @staticmethod
    def _map_status(status: str | None, lifecycle: Lifecycles | None) -> V10EnumStatus:
        if status:
            status_lower = status.lower()
            if "ontwikkeling" in status_lower or "development" in status_lower:
                return V10EnumStatus.IN_ONTWIKKELING
            elif "buiten" in status_lower or "retired" in status_lower or "decommissioned" in status_lower:
                return V10EnumStatus.BUITEN_GEBRUIK
            elif "gebruik" in status_lower or "production" in status_lower or "use" in status_lower:
                return V10EnumStatus.IN_GEBRUIK

        if lifecycle == Lifecycles.DEVELOPMENT:
            return V10EnumStatus.IN_ONTWIKKELING
        elif lifecycle in (
            Lifecycles.IMPLEMENTATION,
            Lifecycles.MONITORING_AND_MANAGEMENT,
        ):
            return V10EnumStatus.IN_GEBRUIK
        elif lifecycle == Lifecycles.PHASING_OUT:
            return V10EnumStatus.BUITEN_GEBRUIK

        return V10EnumStatus.IN_ONTWIKKELING

    @staticmethod
    def _format_date(date_value: Any) -> str | None:  # noqa: ANN401
        if date_value is None:
            return None
        if isinstance(date_value, str):
            if len(date_value) >= 7 and date_value[4] == "-":
                return date_value[:7]
            return date_value
        iso_date = date_value.isoformat()
        if len(iso_date) >= 7:
            return iso_date[:7]
        return iso_date

    @staticmethod
    def _get_contact_email(system_card: AlgorithmSystemCard, organization: Organization) -> str:
        if system_card.owners and len(system_card.owners) > 0:
            email = system_card.owners[0].email
            if email:
                return email

        return "noreply@example.com"

    @staticmethod
    def _get_website(system_card: AlgorithmSystemCard, organization: Organization) -> str | None:
        if system_card.upl:
            return system_card.upl

        return None

    @staticmethod
    def _map_publication_category(
        system_card: AlgorithmSystemCard,
    ) -> V10EnumPublicationCategory:
        if system_card.ai_act_profile:
            risk_group = getattr(system_card.ai_act_profile, "risk_group", None)
            if risk_group == RiskGroup.HOOG_RISICO_AI.value:
                return V10EnumPublicationCategory.HOOG_MINUS_RISICO_AI_MINUS_SYSTEEM

        return V10EnumPublicationCategory.OVERIGE_ALGORITMES

    @staticmethod
    def _get_url(system_card: AlgorithmSystemCard) -> str | None:
        if system_card.references and len(system_card.references) > 0:
            first_ref = system_card.references[0]
            if hasattr(first_ref, "link") and first_ref.link:
                return first_ref.link

        return None

    @staticmethod
    def _get_lawful_basis_text(system_card: AlgorithmSystemCard) -> str | None:
        if not system_card.legal_base:
            return None

        texts: list[str] = []
        for item in system_card.legal_base:
            if hasattr(item, "name") and item.name:
                texts.append(item.name)

        return "\n".join(texts) if texts else None

    @staticmethod
    def _get_lawful_basis_grouping(
        system_card: AlgorithmSystemCard,
    ) -> list[Any] | None:
        if not system_card.legal_base:
            return None

        grouping: list[V10ObjectLawfulBasisGrouping] = []
        for item in system_card.legal_base:
            if hasattr(item, "name") and hasattr(item, "link") and item.name and item.link:
                grouping.append(V10ObjectLawfulBasisGrouping(title=item.name, link=item.link))

        return grouping if grouping else None

    @staticmethod
    def _get_impacttoetsen_grouping(
        system_card: AlgorithmSystemCard,
    ) -> list[Any] | None:
        if not system_card.assessments:
            return None

        grouping: list[V10ObjectImpacttoetsenGrouping] = []
        for assessment in system_card.assessments:
            if hasattr(assessment, "name") and assessment.name:
                link: str | None = None
                if hasattr(assessment, "contents") and assessment.contents:
                    for content in assessment.contents:
                        if hasattr(content, "urn") and content.urn:
                            link = content.urn
                            break

                grouping.append(V10ObjectImpacttoetsenGrouping(title=assessment.name, link=link))

        return grouping if grouping else None

    @staticmethod
    def _get_impacttoetsen_text(system_card: AlgorithmSystemCard) -> str | None:
        if not system_card.assessments:
            return None

        texts: list[str] = []
        for assessment in system_card.assessments:
            if hasattr(assessment, "name") and assessment.name:
                texts.append(assessment.name)

        return ", ".join(texts) if texts else None

    @staticmethod
    def _get_source_data_grouping(system_card: AlgorithmSystemCard) -> list[Any] | None:
        if not system_card.references:
            return None

        grouping: list[V10ObjectSourceDataGrouping] = []
        for ref in system_card.references:
            if hasattr(ref, "name") and hasattr(ref, "link") and ref.name and ref.link:
                grouping.append(V10ObjectSourceDataGrouping(title=ref.name, link=ref.link))

        return grouping if grouping else None

    @staticmethod
    def _get_provider(system_card: AlgorithmSystemCard) -> str | None:
        if system_card.external_providers and len(system_card.external_providers) > 0:
            provider = system_card.external_providers[0]
            if isinstance(provider, str):
                return provider
            elif hasattr(provider, "name"):
                return provider.name

        return None

    @staticmethod
    def _get_publiccode(system_card: AlgorithmSystemCard) -> str | None:
        if system_card.models and len(system_card.models) > 0:
            for model in system_card.models:
                uri = getattr(model, "uri", None)
                if uri:
                    return str(uri)

        if system_card.references:
            for ref in system_card.references:
                if (
                    hasattr(ref, "link")
                    and ref.link
                    and ("github.com" in ref.link.lower() or "gitlab.com" in ref.link.lower())
                ):
                    return ref.link

        return None

    @staticmethod
    def _get_tags(system_card: AlgorithmSystemCard) -> str | None:
        if not system_card.labels:
            return None

        tags: list[str] = []
        for label in system_card.labels:
            if hasattr(label, "name") and label.name:
                tags.append(label.name)

        return ", ".join(tags) if tags else None
