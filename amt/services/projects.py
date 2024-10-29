import json
import logging
from functools import lru_cache
from os import listdir
from os.path import isfile, join
from pathlib import Path
from typing import Annotated

from fastapi import Depends

from amt.core.exceptions import AMTNotFound
from amt.models import Project
from amt.repositories.projects import ProjectsRepository
from amt.schema.instrument import InstrumentBase
from amt.schema.project import ProjectNew
from amt.schema.system_card import AiActProfile, SystemCard
from amt.services.instruments import InstrumentsService
from amt.services.task_registry import get_requirements_and_measures
from amt.services.tasks import TasksService

logger = logging.getLogger(__name__)

template_path = "resources/system_card_templates"


class ProjectsService:
    def __init__(
        self,
        repository: Annotated[ProjectsRepository, Depends(ProjectsRepository)],
        task_service: Annotated[TasksService, Depends(TasksService)],
        instrument_service: Annotated[InstrumentsService, Depends(InstrumentsService)],
    ) -> None:
        self.repository = repository
        self.instrument_service = instrument_service
        self.task_service = task_service

    async def get(self, project_id: int) -> Project:
        project = await self.repository.find_by_id(project_id)
        return project

    async def create(self, project_new: ProjectNew) -> Project:
        system_card_from_template = None
        if project_new.template_id:
            template_files = get_template_files()
            if project_new.template_id in template_files:
                with open(Path(template_path) / Path(template_files[project_new.template_id]["value"])) as f:
                    system_card_from_template = json.load(f)
            else:
                raise AMTNotFound()

        instruments: list[InstrumentBase] = [
            InstrumentBase(urn=instrument_urn) for instrument_urn in project_new.instruments
        ]

        ai_act_profile = AiActProfile(
            type=project_new.type,
            open_source=project_new.open_source,
            publication_category=project_new.publication_category,
            systemic_risk=project_new.systemic_risk,
            transparency_obligations=project_new.transparency_obligations,
            role=project_new.role,
        )

        requirements, measures = get_requirements_and_measures(ai_act_profile)

        system_card = SystemCard(
            name=project_new.name,
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

        project = Project(name=project_new.name, lifecycle=project_new.lifecycle, system_card=system_card)
        project = await self.update(project)

        selected_instruments = self.instrument_service.fetch_instruments(
            [instrument.urn for instrument in project.system_card.instruments]
        )
        for instrument in selected_instruments:
            await self.task_service.create_instrument_tasks(instrument.tasks, project)

        return project

    async def paginate(
        self, skip: int, limit: int, search: str, filters: dict[str, str], sort: dict[str, str]
    ) -> list[Project]:
        projects = await self.repository.paginate(skip=skip, limit=limit, search=search, filters=filters, sort=sort)
        return projects

    async def update(self, project: Project) -> Project:
        # TODO: Is this the right place to sync system cards: system_card and system_card_json?
        project.sync_system_card()
        project = await self.repository.save(project)
        return project


@lru_cache
def get_template_files() -> dict[str, dict[str, str]]:
    return {
        str(i): {"display_value": k.split(".")[0].replace("_", " "), "value": k}
        for i, k in enumerate(listdir(template_path))
        if isfile(join(template_path, k))
    }
