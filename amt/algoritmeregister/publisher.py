from dataclasses import dataclass
from typing import Any

from amt.algoritmeregister.auth import get_access_token
from amt.algoritmeregister.mapper import AlgorithmMapper
from amt.algoritmeregister.openapi.v1_0.client.openapi_client import (
    ApiClient,
    Configuration,
)
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.api.acties_api import (
    ActiesApi,
)
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.api.algoritmes_in_ontwikkeling_api import (
    AlgoritmesInOntwikkelingApi,
)
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.algorithm_summary import (
    AlgorithmSummary,
)
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.preview_url import (
    PreviewUrl,
)
from amt.algoritmeregister.openapi.v1_0.client_extensions import ActiesApiExtensions
from amt.core.config import get_settings
from amt.models.algorithm import Algorithm


class PublicationException(Exception):
    pass


@dataclass
class PublicationResult:
    lars_code: str
    message: str
    response: Any


@dataclass
class ReleaseResult:
    message: str
    response: Any


@dataclass
class PreviewResult:
    preview_url: str
    message: str
    response: PreviewUrl


async def publish_algorithm(
    algorithm: Algorithm, username: str, password: str, organisation_id: str, organisation_name: str
) -> PublicationResult:
    """
    Publish an algorithm to the Algoritmeregister.

    Args:
        algorithm: The algorithm instance to publish
        username: Algoritmeregister username (email address)
        password: Algoritmeregister password
        organisation_id: Organization ID in the Algoritmeregister
        organisation_name: Organization name in the Algoritmeregister

    Returns:
        PublicationResult containing lars_code, message, and response

    Raises:
        PublicationException: If publication fails
    """
    publication_data = AlgorithmMapper.to_publication_model(algorithm, organisation_name)

    settings = get_settings()
    access_token = await get_access_token(username, password)
    configuration = Configuration(host=settings.ALGORITMEREGISTER_API_URL, access_token=access_token)
    configuration.verify_ssl = settings.VERIFY_SSL

    with ApiClient(configuration) as api_client:
        api_instance = AlgoritmesInOntwikkelingApi(api_client)

        try:
            response = api_instance.create_one_algorithm(organisation_id=organisation_id, algorithm_in=publication_data)

            return PublicationResult(
                lars_code=response.lars_code,
                message="Algorithm successfully published to Algoritmeregister",
                response=response,
            )
        except Exception as e:
            raise PublicationException(f"Failed to publish algorithm: {e!s}") from e


async def update_algorithm(
    algorithm: Algorithm,
    username: str,
    password: str,
    organisation_id: str,
    organisation_name: str,
    algorithm_id: str,
) -> PublicationResult:
    """
    Update an existing algorithm in the Algoritmeregister.

    Args:
        algorithm: The algorithm instance to update
        username: Algoritmeregister username (email address)
        password: Algoritmeregister password
        organisation_id: Organization ID in the Algoritmeregister
        organisation_name: Organization name in the Algoritmeregister
        algorithm_id: The ID of the algorithm to update

    Returns:
        PublicationResult containing lars_code, message, and response

    Raises:
        PublicationException: If update fails
    """
    publication_data = AlgorithmMapper.to_publication_model(algorithm, organisation_name)

    settings = get_settings()
    access_token = await get_access_token(username, password)
    configuration = Configuration(host=settings.ALGORITMEREGISTER_API_URL, access_token=access_token)
    configuration.verify_ssl = settings.VERIFY_SSL

    with ApiClient(configuration) as api_client:
        api_instance = AlgoritmesInOntwikkelingApi(api_client)

        try:
            response = api_instance.update_one_algorithm(
                organisation_id=organisation_id,
                algorithm_id=algorithm_id,
                algorithm_in=publication_data,
            )

            return PublicationResult(
                lars_code=algorithm_id,
                message="Algorithm successfully updated in Algoritmeregister",
                response=response,
            )
        except Exception as e:
            raise PublicationException(f"Failed to update algorithm: {e!s}") from e


async def get_algorithms_status(
    username: str, password: str, organisation_id: str, lars_code: str | None = None
) -> list[AlgorithmSummary]:
    """
    Get algorithms status from the Algoritmeregister for the given organization.

    Args:
        username: Algoritmeregister username (email address)
        password: Algoritmeregister password
        organisation_id: Organization ID in the Algoritmeregister
        lars_code: Optional LARS code to filter for a specific algorithm

    Returns:
        List of AlgorithmSummary objects (filtered to one item if lars_code is provided)

    Raises:
        PublicationException: If retrieval fails
    """
    settings = get_settings()
    access_token = await get_access_token(username, password)
    configuration = Configuration(host=settings.ALGORITMEREGISTER_API_URL, access_token=access_token)
    configuration.verify_ssl = settings.VERIFY_SSL

    with ApiClient(configuration) as api_client:
        api_instance = AlgoritmesInOntwikkelingApi(api_client)

        try:
            response = api_instance.get_all_algorithms(organisation_id=organisation_id)

            if lars_code:
                return [algorithm for algorithm in response if algorithm.lars == lars_code]
            else:
                return response
        except Exception as e:
            raise PublicationException(f"Failed to get algorithms status: {e!s}") from e


async def preview_algorithm(username: str, password: str, organisation_id: str, lars_code: str) -> PreviewResult:
    """
    Get a preview URL for an algorithm.

    This retrieves a URL to preview the latest data of an algorithm.

    Args:
        username: Algoritmeregister username (email address)
        password: Algoritmeregister password
        organisation_id: Organization ID in the Algoritmeregister
        lars_code: The LARS code of the algorithm to preview

    Returns:
        PreviewResult containing preview URL, message, and response

    Raises:
        PublicationException: If preview fails
    """
    settings = get_settings()
    access_token = await get_access_token(username, password)
    configuration = Configuration(host=settings.ALGORITMEREGISTER_API_URL, access_token=access_token)
    configuration.verify_ssl = settings.VERIFY_SSL

    with ApiClient(configuration) as api_client:
        api_instance = ActiesApi(api_client)

        try:
            response = api_instance.get_one_preview_url(organisation_id=organisation_id, algorithm_id=lars_code)

            return PreviewResult(
                preview_url=response.url,
                message="Preview URL successfully retrieved",
                response=response,
            )
        except Exception as e:
            raise PublicationException(f"Failed to get preview URL: {e!s}") from e


async def release_algorithm(username: str, password: str, organisation_id: str, lars_code: str) -> ReleaseResult:
    """
    Release an algorithm (STATE_1 → STATE_2).

    This transitions the algorithm from "In bewerking" to "Vrijgegeven" state.
    Requires role_1 (Redacteur) permission.

    Args:
        username: Algoritmeregister username (email address)
        password: Algoritmeregister password
        organisation_id: Organization ID in the Algoritmeregister
        lars_code: The LARS code of the algorithm to release

    Returns:
        ReleaseResult containing message and response

    Raises:
        PublicationException: If release fails
    """
    settings = get_settings()
    access_token = await get_access_token(username, password)
    configuration = Configuration(host=settings.ALGORITMEREGISTER_API_URL, access_token=access_token)
    configuration.verify_ssl = settings.VERIFY_SSL

    with ApiClient(configuration) as api_client:
        api_instance = ActiesApi(api_client)

        try:
            response = api_instance.release_one_algorithm(organisation_id=organisation_id, algorithm_id=lars_code)

            return ReleaseResult(
                message="Algorithm successfully released (transitioned to STATE_2)",
                response=response,
            )
        except Exception as e:
            raise PublicationException(f"Failed to release algorithm: {e!s}") from e


async def publish_algorithm_final(username: str, password: str, organisation_id: str, lars_code: str) -> ReleaseResult:
    """
    Publish an algorithm (STATE_2 → PUBLISHED).

    This transitions the algorithm from "Vrijgegeven" to "Gepubliceerd" state.
    Requires ICTU role permission.

    Note: This endpoint is hidden from the OpenAPI spec but is functional.

    Args:
        username: Algoritmeregister username (email address)
        password: Algoritmeregister password
        organisation_id: Organization ID in the Algoritmeregister
        lars_code: The LARS code of the algorithm to publish

    Returns:
        ReleaseResult containing message and response

    Raises:
        PublicationException: If publication fails
    """
    settings = get_settings()
    access_token = await get_access_token(username, password)
    configuration = Configuration(host=settings.ALGORITMEREGISTER_API_URL, access_token=access_token)
    configuration.verify_ssl = settings.VERIFY_SSL

    with ApiClient(configuration) as api_client:
        api_extensions = ActiesApiExtensions(api_client)

        try:
            response = api_extensions.publish_one_algorithm(organisation_id=organisation_id, algorithm_id=lars_code)

            return ReleaseResult(
                message="Algorithm successfully published (transitioned to PUBLISHED)",
                response=response,
            )
        except Exception as e:
            raise PublicationException(f"Failed to publish algorithm: {e!s}") from e
