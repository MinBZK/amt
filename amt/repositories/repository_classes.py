import logging
from abc import ABC

from amt.repositories.deps import AsyncSessionWithCommitFlag

logger = logging.getLogger(__name__)


class BaseRepository(ABC):  # noqa: B024
    """Abstract base class for all repositories

    This classes is currently only used for type testing.
    """

    def __init__(self, session: AsyncSessionWithCommitFlag) -> None:
        self.session = session
        logger.debug(
            f"Repository {self.__class__.__name__} uses session: {self.session.info.get('id', 'unknown')}"
            f" / {self.session}"
        )
