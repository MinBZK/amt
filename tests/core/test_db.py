from unittest.mock import Mock, patch

import pytest
from sqlmodel import Session, select
from tad.core.db import check_db


@pytest.mark.skip(reason="not working yet")
async def test_check_dabase():
    mock_session = Mock(spec=Session)

    with patch("sqlmodel.Session", return_value=mock_session):
        await check_db()

    assert mock_session.exec.assert_called_once_with(select(1))
