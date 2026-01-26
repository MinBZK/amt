from unittest.mock import MagicMock

import pytest
from amt.algoritmeregister.publisher import (
    PreviewResult,
    PublicationException,
    PublicationResult,
    ReleaseResult,
    get_algorithms_status,
    preview_algorithm,
    publish_algorithm,
    publish_algorithm_final,
    release_algorithm,
    update_algorithm,
)
from pytest_mock import MockerFixture

from tests.constants import default_algorithm, default_organization

TEST_PASSWORD = "testpass"  # noqa: S105


def create_test_algorithm():
    """Create a test algorithm with an attached organization for publisher tests."""
    organization = default_organization()
    algorithm = default_algorithm()
    algorithm.organization = organization
    return algorithm


@pytest.mark.asyncio
async def test_publish_algorithm_success(mocker: MockerFixture) -> None:
    # given
    algorithm = create_test_algorithm()

    mock_response = MagicMock()
    mock_response.lars_code = "LARS123"

    mocker.patch("amt.algoritmeregister.publisher.get_access_token", return_value="test_token")
    mocker.patch(
        "amt.algoritmeregister.publisher.get_settings",
        return_value=MagicMock(
            ALGORITMEREGISTER_API_URL="https://api.test.com",
            VERIFY_SSL=True,
        ),
    )
    mock_api_instance = MagicMock()
    mock_api_instance.create_one_algorithm.return_value = mock_response
    mocker.patch("amt.algoritmeregister.publisher.AlgoritmesInOntwikkelingApi", return_value=mock_api_instance)

    # when
    result = await publish_algorithm(
        algorithm=algorithm,
        username="test@example.com",
        password=TEST_PASSWORD,
        organisation_id="ORG1",
        organisation_name="Test Organisation",
    )

    # then
    assert isinstance(result, PublicationResult)
    assert result.lars_code == "LARS123"
    assert result.message == "Algorithm successfully published to Algoritmeregister"


@pytest.mark.asyncio
async def test_publish_algorithm_failure(mocker: MockerFixture) -> None:
    # given
    algorithm = create_test_algorithm()

    mocker.patch("amt.algoritmeregister.publisher.get_access_token", return_value="test_token")
    mocker.patch(
        "amt.algoritmeregister.publisher.get_settings",
        return_value=MagicMock(
            ALGORITMEREGISTER_API_URL="https://api.test.com",
            VERIFY_SSL=True,
        ),
    )
    mock_api_instance = MagicMock()
    mock_api_instance.create_one_algorithm.side_effect = Exception("API Error")
    mocker.patch("amt.algoritmeregister.publisher.AlgoritmesInOntwikkelingApi", return_value=mock_api_instance)

    # when / then
    with pytest.raises(PublicationException) as exc_info:
        await publish_algorithm(
            algorithm=algorithm,
            username="test@example.com",
            password=TEST_PASSWORD,
            organisation_id="ORG1",
            organisation_name="Test Organisation",
        )
    assert "Failed to publish algorithm" in str(exc_info.value)


@pytest.mark.asyncio
async def test_update_algorithm_success(mocker: MockerFixture) -> None:
    # given
    algorithm = create_test_algorithm()

    mock_response = MagicMock()

    mocker.patch("amt.algoritmeregister.publisher.get_access_token", return_value="test_token")
    mocker.patch(
        "amt.algoritmeregister.publisher.get_settings",
        return_value=MagicMock(
            ALGORITMEREGISTER_API_URL="https://api.test.com",
            VERIFY_SSL=True,
        ),
    )
    mock_api_instance = MagicMock()
    mock_api_instance.update_one_algorithm.return_value = mock_response
    mocker.patch("amt.algoritmeregister.publisher.AlgoritmesInOntwikkelingApi", return_value=mock_api_instance)

    # when
    result = await update_algorithm(
        algorithm=algorithm,
        username="test@example.com",
        password=TEST_PASSWORD,
        organisation_id="ORG1",
        organisation_name="Test Organisation",
        algorithm_id="LARS123",
    )

    # then
    assert isinstance(result, PublicationResult)
    assert result.lars_code == "LARS123"
    assert result.message == "Algorithm successfully updated in Algoritmeregister"


@pytest.mark.asyncio
async def test_update_algorithm_failure(mocker: MockerFixture) -> None:
    # given
    algorithm = create_test_algorithm()

    mocker.patch("amt.algoritmeregister.publisher.get_access_token", return_value="test_token")
    mocker.patch(
        "amt.algoritmeregister.publisher.get_settings",
        return_value=MagicMock(
            ALGORITMEREGISTER_API_URL="https://api.test.com",
            VERIFY_SSL=True,
        ),
    )
    mock_api_instance = MagicMock()
    mock_api_instance.update_one_algorithm.side_effect = Exception("API Error")
    mocker.patch("amt.algoritmeregister.publisher.AlgoritmesInOntwikkelingApi", return_value=mock_api_instance)

    # when / then
    with pytest.raises(PublicationException) as exc_info:
        await update_algorithm(
            algorithm=algorithm,
            username="test@example.com",
            password=TEST_PASSWORD,
            organisation_id="ORG1",
            organisation_name="Test Organisation",
            algorithm_id="LARS123",
        )
    assert "Failed to update algorithm" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_algorithms_status_success(mocker: MockerFixture) -> None:
    # given
    mock_algorithm_summary = MagicMock()
    mock_algorithm_summary.lars = "LARS123"

    mocker.patch("amt.algoritmeregister.publisher.get_access_token", return_value="test_token")
    mocker.patch(
        "amt.algoritmeregister.publisher.get_settings",
        return_value=MagicMock(
            ALGORITMEREGISTER_API_URL="https://api.test.com",
            VERIFY_SSL=True,
        ),
    )
    mock_api_instance = MagicMock()
    mock_api_instance.get_all_algorithms.return_value = [mock_algorithm_summary]
    mocker.patch("amt.algoritmeregister.publisher.AlgoritmesInOntwikkelingApi", return_value=mock_api_instance)

    # when
    result = await get_algorithms_status(
        username="test@example.com",
        password=TEST_PASSWORD,
        organisation_id="ORG1",
    )

    # then
    assert len(result) == 1
    assert result[0].lars == "LARS123"


@pytest.mark.asyncio
async def test_get_algorithms_status_with_lars_filter(mocker: MockerFixture) -> None:
    # given
    mock_algorithm_1 = MagicMock()
    mock_algorithm_1.lars = "LARS123"
    mock_algorithm_2 = MagicMock()
    mock_algorithm_2.lars = "LARS456"

    mocker.patch("amt.algoritmeregister.publisher.get_access_token", return_value="test_token")
    mocker.patch(
        "amt.algoritmeregister.publisher.get_settings",
        return_value=MagicMock(
            ALGORITMEREGISTER_API_URL="https://api.test.com",
            VERIFY_SSL=True,
        ),
    )
    mock_api_instance = MagicMock()
    mock_api_instance.get_all_algorithms.return_value = [mock_algorithm_1, mock_algorithm_2]
    mocker.patch("amt.algoritmeregister.publisher.AlgoritmesInOntwikkelingApi", return_value=mock_api_instance)

    # when
    result = await get_algorithms_status(
        username="test@example.com",
        password=TEST_PASSWORD,
        organisation_id="ORG1",
        lars_code="LARS123",
    )

    # then
    assert len(result) == 1
    assert result[0].lars == "LARS123"


@pytest.mark.asyncio
async def test_get_algorithms_status_failure(mocker: MockerFixture) -> None:
    # given
    mocker.patch("amt.algoritmeregister.publisher.get_access_token", return_value="test_token")
    mocker.patch(
        "amt.algoritmeregister.publisher.get_settings",
        return_value=MagicMock(
            ALGORITMEREGISTER_API_URL="https://api.test.com",
            VERIFY_SSL=True,
        ),
    )
    mock_api_instance = MagicMock()
    mock_api_instance.get_all_algorithms.side_effect = Exception("API Error")
    mocker.patch("amt.algoritmeregister.publisher.AlgoritmesInOntwikkelingApi", return_value=mock_api_instance)

    # when / then
    with pytest.raises(PublicationException) as exc_info:
        await get_algorithms_status(
            username="test@example.com",
            password=TEST_PASSWORD,
            organisation_id="ORG1",
        )
    assert "Failed to get algorithms status" in str(exc_info.value)


@pytest.mark.asyncio
async def test_preview_algorithm_success(mocker: MockerFixture) -> None:
    # given
    mock_response = MagicMock()
    mock_response.url = "https://preview.example.com/algorithm/123"

    mocker.patch("amt.algoritmeregister.publisher.get_access_token", return_value="test_token")
    mocker.patch(
        "amt.algoritmeregister.publisher.get_settings",
        return_value=MagicMock(
            ALGORITMEREGISTER_API_URL="https://api.test.com",
            VERIFY_SSL=True,
        ),
    )
    mock_api_instance = MagicMock()
    mock_api_instance.get_one_preview_url.return_value = mock_response
    mocker.patch("amt.algoritmeregister.publisher.ActiesApi", return_value=mock_api_instance)

    # when
    result = await preview_algorithm(
        username="test@example.com",
        password=TEST_PASSWORD,
        organisation_id="ORG1",
        lars_code="LARS123",
    )

    # then
    assert isinstance(result, PreviewResult)
    assert result.preview_url == "https://preview.example.com/algorithm/123"
    assert result.message == "Preview URL successfully retrieved"


@pytest.mark.asyncio
async def test_preview_algorithm_failure(mocker: MockerFixture) -> None:
    # given
    mocker.patch("amt.algoritmeregister.publisher.get_access_token", return_value="test_token")
    mocker.patch(
        "amt.algoritmeregister.publisher.get_settings",
        return_value=MagicMock(
            ALGORITMEREGISTER_API_URL="https://api.test.com",
            VERIFY_SSL=True,
        ),
    )
    mock_api_instance = MagicMock()
    mock_api_instance.get_one_preview_url.side_effect = Exception("API Error")
    mocker.patch("amt.algoritmeregister.publisher.ActiesApi", return_value=mock_api_instance)

    # when / then
    with pytest.raises(PublicationException) as exc_info:
        await preview_algorithm(
            username="test@example.com",
            password=TEST_PASSWORD,
            organisation_id="ORG1",
            lars_code="LARS123",
        )
    assert "Failed to get preview URL" in str(exc_info.value)


@pytest.mark.asyncio
async def test_release_algorithm_success(mocker: MockerFixture) -> None:
    # given
    mock_response = MagicMock()

    mocker.patch("amt.algoritmeregister.publisher.get_access_token", return_value="test_token")
    mocker.patch(
        "amt.algoritmeregister.publisher.get_settings",
        return_value=MagicMock(
            ALGORITMEREGISTER_API_URL="https://api.test.com",
            VERIFY_SSL=True,
        ),
    )
    mock_api_instance = MagicMock()
    mock_api_instance.release_one_algorithm.return_value = mock_response
    mocker.patch("amt.algoritmeregister.publisher.ActiesApi", return_value=mock_api_instance)

    # when
    result = await release_algorithm(
        username="test@example.com",
        password=TEST_PASSWORD,
        organisation_id="ORG1",
        lars_code="LARS123",
    )

    # then
    assert isinstance(result, ReleaseResult)
    assert result.message == "Algorithm successfully released (transitioned to STATE_2)"


@pytest.mark.asyncio
async def test_release_algorithm_failure(mocker: MockerFixture) -> None:
    # given
    mocker.patch("amt.algoritmeregister.publisher.get_access_token", return_value="test_token")
    mocker.patch(
        "amt.algoritmeregister.publisher.get_settings",
        return_value=MagicMock(
            ALGORITMEREGISTER_API_URL="https://api.test.com",
            VERIFY_SSL=True,
        ),
    )
    mock_api_instance = MagicMock()
    mock_api_instance.release_one_algorithm.side_effect = Exception("API Error")
    mocker.patch("amt.algoritmeregister.publisher.ActiesApi", return_value=mock_api_instance)

    # when / then
    with pytest.raises(PublicationException) as exc_info:
        await release_algorithm(
            username="test@example.com",
            password=TEST_PASSWORD,
            organisation_id="ORG1",
            lars_code="LARS123",
        )
    assert "Failed to release algorithm" in str(exc_info.value)


@pytest.mark.asyncio
async def test_publish_algorithm_final_success(mocker: MockerFixture) -> None:
    # given
    mock_response = MagicMock()

    mocker.patch("amt.algoritmeregister.publisher.get_access_token", return_value="test_token")
    mocker.patch(
        "amt.algoritmeregister.publisher.get_settings",
        return_value=MagicMock(
            ALGORITMEREGISTER_API_URL="https://api.test.com",
            VERIFY_SSL=True,
        ),
    )
    mock_api_extensions = MagicMock()
    mock_api_extensions.publish_one_algorithm.return_value = mock_response
    mocker.patch("amt.algoritmeregister.publisher.ActiesApiExtensions", return_value=mock_api_extensions)

    # when
    result = await publish_algorithm_final(
        username="test@example.com",
        password=TEST_PASSWORD,
        organisation_id="ORG1",
        lars_code="LARS123",
    )

    # then
    assert isinstance(result, ReleaseResult)
    assert result.message == "Algorithm successfully published (transitioned to PUBLISHED)"


@pytest.mark.asyncio
async def test_publish_algorithm_final_failure(mocker: MockerFixture) -> None:
    # given
    mocker.patch("amt.algoritmeregister.publisher.get_access_token", return_value="test_token")
    mocker.patch(
        "amt.algoritmeregister.publisher.get_settings",
        return_value=MagicMock(
            ALGORITMEREGISTER_API_URL="https://api.test.com",
            VERIFY_SSL=True,
        ),
    )
    mock_api_extensions = MagicMock()
    mock_api_extensions.publish_one_algorithm.side_effect = Exception("API Error")
    mocker.patch("amt.algoritmeregister.publisher.ActiesApiExtensions", return_value=mock_api_extensions)

    # when / then
    with pytest.raises(PublicationException) as exc_info:
        await publish_algorithm_final(
            username="test@example.com",
            password=TEST_PASSWORD,
            organisation_id="ORG1",
            lars_code="LARS123",
        )
    assert "Failed to publish algorithm" in str(exc_info.value)
