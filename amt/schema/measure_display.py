from pydantic import Field

from amt.schema.measure import ExtendedMeasureTask
from amt.schema.user import User


class DisplayMeasureTask(ExtendedMeasureTask):
    """
    Class used to display a measure task, so it includes resolved fields that should
    not be stored!
    """

    users: list[User] = Field(default_factory=list)
