import json
import logging
from datetime import datetime
from functools import lru_cache
from os import listdir
from os.path import isfile, join
from pathlib import Path
from typing import Annotated
from uuid import UUID

from fastapi import Depends

from amt.core.exceptions import AMTNotFound
from amt.models import Algorithm
from amt.repositories.algorithms import AlgorithmsRepository
from amt.repositories.organizations import OrganizationsRepository
from amt.schema.algorithm import AlgorithmNew
from amt.schema.instrument import InstrumentBase
from amt.schema.system_card import AiActProfile, SystemCard
from amt.services.instruments import InstrumentsService, create_instrument_service
from amt.services.task_registry import get_requirements_and_measures

logger = logging.getLogger(__name__)

template_path = "resources/system_card_templates"


class AlgorithmsService:
    def __init__(
        self,
        repository: Annotated[AlgorithmsRepository, Depends(AlgorithmsRepository)],
        instrument_service: Annotated[InstrumentsService, Depends(create_instrument_service)],
        organizations_repository: Annotated[OrganizationsRepository, Depends(OrganizationsRepository)],
    ) -> None:
        self.repository = repository
        self.instrument_service = instrument_service
        self.organizations_repository = organizations_repository

    async def get(self, algorithm_id: int) -> Algorithm:
        algorithm = await self.repository.find_by_id(algorithm_id)
        if algorithm.deleted_at:
            raise AMTNotFound()
        return algorithm

    async def delete(self, algorithm_id: int) -> Algorithm:
        algorithm = await self.repository.find_by_id(algorithm_id)
        algorithm.deleted_at = datetime.now(tz=None)  # noqa: DTZ005
        algorithm = await self.repository.save(algorithm)
        return algorithm

    async def create(self, algorithm_new: AlgorithmNew, user_id: UUID | str) -> Algorithm:
        system_card_from_template = None
        if algorithm_new.template_id:
            template_files = get_template_files()
            if algorithm_new.template_id in template_files:
                with open(Path(template_path) / Path(template_files[algorithm_new.template_id]["value"])) as f:
                    system_card_from_template = json.load(f)
            else:
                raise AMTNotFound()

        instruments: list[InstrumentBase] = [
            InstrumentBase(urn=instrument_urn) for instrument_urn in algorithm_new.instruments
        ]

        ai_act_profile = AiActProfile(
            type=algorithm_new.type,
            open_source=algorithm_new.open_source,
            risk_group=algorithm_new.risk_group,
            conformity_assessment_body=algorithm_new.conformity_assessment_body,
            systemic_risk=algorithm_new.systemic_risk,
            transparency_obligations=algorithm_new.transparency_obligations,
            role=algorithm_new.role,
        )

        requirements, measures = await get_requirements_and_measures(ai_act_profile)

        system_card = SystemCard(
            name=algorithm_new.name,
            ai_act_profile=ai_act_profile,
            instruments=instruments,
            requirements=requirements,
            measures=measures,
        )

        if system_card_from_template is not None:
            system_card_dict = system_card.model_dump()
            system_card_merged = {
                k: (
                    system_card_dict[k]
                    if k in system_card_dict and system_card_dict.get(k)
                    else system_card_from_template.get(k)
                )
                for k in set(system_card_dict) | set(system_card_from_template)
            }
            system_card_merged["ai_act_profile"] = {
                k: (
                    system_card_dict["ai_act_profile"][k]
                    if k in system_card_dict["ai_act_profile"] and system_card_dict["ai_act_profile"].get(k)
                    else system_card_from_template["ai_act_profile"].get(k)
                )
                for k in set(system_card_dict["ai_act_profile"]) | set(system_card_from_template["ai_act_profile"])
            }
            system_card = SystemCard.model_validate(system_card_merged)

        algorithm = Algorithm(name=algorithm_new.name, lifecycle=algorithm_new.lifecycle, system_card=system_card)
        algorithm.organization = await self.organizations_repository.find_by_id_and_user_id(
            algorithm_new.organization_id, user_id
        )

        algorithm = await self.update(algorithm)

        return algorithm

    async def paginate(
        self, skip: int, limit: int, search: str, filters: dict[str, str], sort: dict[str, str]
    ) -> list[Algorithm]:
        algorithms = await self.repository.paginate(skip=skip, limit=limit, search=search, filters=filters, sort=sort)
        return algorithms

    async def update(self, algorithm: Algorithm) -> Algorithm:
        # TODO: Is this the right place to sync system cards: system_card and system_card_json?
        algorithm.sync_system_card()
        algorithm = await self.repository.save(algorithm)
        return algorithm


@lru_cache
def get_template_files() -> dict[str, dict[str, str]]:
    return {
        str(i): {"display_value": k.split(".")[0].replace("_", " "), "value": k}
        for i, k in enumerate(listdir(template_path))
        if isfile(join(template_path, k))
    }
