import logging
from typing import Annotated

from fastapi import Depends

from amt.models import Project
from amt.repositories.projects import ProjectsRepository
from amt.schema.instrument import InstrumentBase
from amt.schema.project import ProjectNew
from amt.schema.system_card import AiActProfile, SystemCard
from amt.services.instruments import InstrumentsService
from amt.services.task_registry import get_requirements_and_measures
from amt.services.tasks import TasksService

logger = logging.getLogger(__name__)


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

    def get(self, project_id: int) -> Project:
        return self.repository.find_by_id(project_id)

    def create(self, project_new: ProjectNew) -> Project:
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

        project = Project(name=project_new.name, lifecycle=project_new.lifecycle, system_card=system_card)
        project = self.update(project)

        selected_instruments = self.instrument_service.fetch_instruments(project_new.instruments)  # type: ignore
        for instrument in selected_instruments:
            self.task_service.create_instrument_tasks(instrument.tasks, project)

        return project

    def paginate(self, skip: int, limit: int, search: str, filters: dict[str, str]) -> list[Project]:
        return self.repository.paginate(skip=skip, limit=limit, search=search, filters=filters)

    def update(self, project: Project) -> Project:
        # TODO: Is this the right place to sync system cards: system_card and system_card_json?
        project.sync_system_card()
        return self.repository.save(project)
