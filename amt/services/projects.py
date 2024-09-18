import logging
from typing import Annotated

from fastapi import Depends

from amt.core.config import get_settings
from amt.models import Project
from amt.repositories.projects import ProjectsRepository
from amt.schema.instrument import InstrumentBase
from amt.schema.project import ProjectNew
from amt.schema.system_card import SystemCard
from amt.services.instruments import InstrumentsService
from amt.services.storage import Storage, StorageFactory
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
        project = Project(name=project_new.name)

        self.repository.save(project)

        system_card_file = get_settings().CARD_DIR / f"{project.id}_system.yaml"

        project.model_card = str(system_card_file)

        project = self.update(project)

        instruments: list[InstrumentBase] = [
            InstrumentBase(urn=instrument_urn) for instrument_urn in project_new.instruments
        ]
        system_card = SystemCard(name=project_new.name, selected_instruments=instruments)

        storage_writer: Storage = StorageFactory.init(
            storage_type="file", location=system_card_file.parent, filename=system_card_file.name
        )
        storage_writer.write(system_card.model_dump())

        selected_instruments = self.instrument_service.fetch_instruments(project_new.instruments)  # type: ignore
        for instrument in selected_instruments:
            self.task_service.create_instrument_tasks(instrument.tasks, project)

        return project

    def paginate(self, skip: int, limit: int, search: str) -> list[Project]:
        return self.repository.paginate(skip=skip, limit=limit, search=search)

    def update(self, project: Project) -> Project:
        return self.repository.save(project)
