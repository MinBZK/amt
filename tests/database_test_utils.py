from typing import Any

from sqlalchemy import text
from sqlmodel import Session, SQLModel
from tad.core.db import get_engine


def enrich_with_default_values(specification: dict[str, Any]) -> dict[str, Any]:
    """
    If a known table dictionary is given, like a task or status, default values will be added
    and an enriched dictionary is returned.
    :param specification: the dictionary to be enriched
    :return: an enriched dictionary
    """
    default_specification = {}
    if specification["table"] == "task":
        default_specification["title"] = "Test task " + str(specification["id"])
        default_specification["description"] = "Test task description " + str(specification["id"])
        default_specification["sort_order"] = specification["id"]
    elif specification["table"] == "status":
        default_specification["name"] = "Status " + str(specification["id"])
        default_specification["sort_order"] = specification["id"]
    return specification | default_specification


def fix_missing_relations(specification: dict[str, Any]) -> None:
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
        if not item_exists(status_specification):
            create_db_entries([status_specification])


def item_exists(specification: dict[str, Any]) -> bool:
    """
    Check if an item exists in the database with the table and id given
    in the dictionary
    :param specification: a dictionary with a table specification
    :return: True if the item exists in the database, False otherwise
    """
    values = ", ".join(
        key + "=" + str(val) if str(val).isnumeric() else str("'" + val + "'")
        for key, val in specification.items()
        if key != "table"
    )
    table = specification["table"]
    statement = f"SELECT COUNT(*) FROM {table} WHERE {values}"  # noqa S608
    with Session(get_engine()) as session:
        result = session.exec(text(statement)).first()
    return result[0] != 0


def create_db_entries(specifications: list[dict[str, Any]]) -> None:
    """
    Given an array of specifications, create the database entries.

    If you want to start with an empty database, use init_db instead!

    See init_db doc for examples.

    :param specifications: an array of dictionaries with table specifications
    :return: None
    """
    for specification in specifications:
        specification = enrich_with_default_values(specification)
        exists_specification = {"table": specification["table"], "id": specification["id"]}
        if not item_exists(exists_specification):
            fix_missing_relations(specification)
            table = specification.pop("table")
            keys = ", ".join(key for key in specification)
            values = ", ".join(
                str(val) if str(val).isnumeric() else str("'" + val + "'") for val in specification.values()
            )
            statement = f"INSERT INTO {table} ({keys}) VALUES ({values})"  # noqa S608
            with Session(get_engine()) as session:
                session.exec(text(statement))
                session.commit()


def init_db(specifications: list[dict[str, Any]]) -> None:
    """
    Drop all database tables and create them. Then fill the database with the
    entries from the array of dictionaries with table specifications.

    Example: [{'table': 'task', 'id': 1 'title': 'Test task 1', 'description': 'Test task description 1'}]

    The example below will be enriched so all required fields for a task will have a value.

    Example: [{'table': 'task', 'id': 1}]

    Example: [{"table": "status", "id": 1},{"table": "task", "id": 1, "status_id": 1}]

    :param specifications: an array of dictionaries with table specifications
    :return: None
    """
    SQLModel.metadata.drop_all(get_engine())
    SQLModel.metadata.create_all(get_engine())
    create_db_entries(specifications)
