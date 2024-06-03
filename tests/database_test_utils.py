from collections.abc import Generator
from typing import Any

from sqlalchemy import text
from sqlmodel import Session, SQLModel
from tad.core.db import get_engine


class DatabaseTestUtils:
    """
    Class to use for testing database calls. On creation, this class destroys and recreates the database tables.
    """

    def __init__(self, session: Generator[Session, Any, Any]):
        self.clear()
        self.session: Generator[Session, Any, Any] = session

    def clear(self) -> None:
        """
        Drops and recreates the database tables.
        :return: None
        """
        SQLModel.metadata.drop_all(get_engine())
        SQLModel.metadata.create_all(get_engine())

    def _enrich_with_default_values(self, specification: dict[str, str | int]) -> dict[str, str | int]:
        """
        If a known table dictionary is given, like a task or status, default values will be added
        and an enriched dictionary is returned.
        :param specification: the dictionary to be enriched
        :return: an enriched dictionary
        """
        default_specification: dict[str, str | int] = {}
        if specification["table"] == "task":
            default_specification["title"] = "Test task " + str(specification["id"])
            default_specification["description"] = "Test task description " + str(specification["id"])
            default_specification["sort_order"] = specification["id"]
            default_specification["status_id"] = 1
        elif specification["table"] == "status":
            default_specification["name"] = "Status " + str(specification["id"])
            default_specification["sort_order"] = specification["id"]
        return default_specification | specification

    def _fix_missing_relations(self, specification: dict[str, Any]) -> None:
        """
        If a dictionary with a known table is given, like a task, the related item,
        for example a status, will be created in the database if the id does not
        exist yet. We do this to comply with database relationships and make it
        easier to set up tests with minimal effort.
        :param specification: a dictionary with a table specification
        :return: None
        """
        if specification["table"] == "task":
            status_specification = {"id": specification["status_id"], "table": "status"}
            if not self.item_exists(status_specification):
                self.init([status_specification])

    def get_items(self, specification: dict[str, str | int]) -> Any:
        """
        Create a query based on the dictionary specification and return the result
        :param specification: a dictionary with a table specification
        :return: the results of the query
        """
        values = ", ".join(
            key + "=" + str(val) if str(val).isnumeric() else str('"' + val + '"')  # type: ignore
            for key, val in specification.items()  # type: ignore
            if key != "table"  # type: ignore
        )
        table = specification["table"]
        statement = f"SELECT * FROM {table} WHERE {values}"  # noqa S608
        return self.session.exec(text(statement)).all()  # type: ignore

    def item_exists(self, specification: dict[str, Any]) -> bool:
        """
        Check if an item exists in the database with the table and id given
        in the dictionary
        :param specification: a dictionary with a table specification
        :return: True if the item exists in the database, False otherwise
        """
        result = self.get_items(specification)
        return len(result) != 0

    def init(self, specifications: list[dict[str, str | int]] | None = None) -> None:
        """
        Given an array of specifications, create the database entries.

        Example: [{'table': 'task', 'id': 1 'title': 'Test task 1', 'description': 'Test task description 1'}]

        The example below will be enriched so all required fields for a task will have a value.

        Example: [{'table': 'task', 'id': 1}]

        Example: [{"table": "status", "id": 1},{"table": "task", "id": 1, "status_id": 1}]

        :param specifications: an array of dictionaries with table specifications
        :return: None
        """
        if specifications is None:
            return
        for specification in specifications:
            specification = self._enrich_with_default_values(specification)
            exists_specification = {"table": specification["table"], "id": specification["id"]}
            if not self.item_exists(exists_specification):
                self._fix_missing_relations(specification)
                table = specification.pop("table")
                keys = ", ".join(key for key in specification)
                values = ", ".join(
                    str(val) if str(val).isnumeric() else str("'" + val + "'")  # type: ignore
                    for val in specification.values()  # type: ignore
                )
                statement = f"INSERT INTO {table} ({keys}) VALUES ({values})"  # noqa S608
                self.session.exec(text(statement))  # type: ignore
                self.session.commit()  # type: ignore
