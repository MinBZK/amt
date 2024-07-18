import logging
from typing import Annotated

from fastapi import Depends

from tad.core.config import get_settings
from tad.models import Project
from tad.repositories.projects import ProjectsRepository
from tad.schema.instrument import InstrumentBase
from tad.schema.project import ProjectNew
from tad.schema.system_card import SystemCard
from tad.services.storage import WriterFactory

logger = logging.getLogger(__name__)


class ProjectsService:
    def __init__(self, repository: Annotated[ProjectsRepository, Depends(ProjectsRepository)]) -> None:
        self.repository = repository

    def get(self, project_id: int) -> Project | None:
        project = None
        try:
            project = self.repository.find_by_id(project_id)
        except Exception:
            project = None

        return project

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

        storage_writer = WriterFactory.get_writer(
            writer_type="file", location=system_card_file.parent, filename=system_card_file.name
        )
        storage_writer.write(system_card.model_dump())

        return project

    def update(self, project: Project) -> Project:
        return self.repository.save(project)
