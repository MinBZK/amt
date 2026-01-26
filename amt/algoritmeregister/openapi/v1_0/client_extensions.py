"""
Custom extensions for the Algoritmeregister OpenAPI client.

This module contains custom API methods that are not included in the generated
client because they are hidden from the OpenAPI specification (include_in_schema=False).
"""

from typing import Annotated, Any

from pydantic import Field, StrictFloat, StrictInt, StrictStr, validate_call

from amt.algoritmeregister.openapi.v1_0.client.openapi_client import ApiClient
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.api_client import RequestSerialized
from amt.algoritmeregister.openapi.v1_0.client.openapi_client.models.algorithm_action_response import (
    AlgorithmActionResponse,
)


class ActiesApiExtensions:
    """
    Extensions for the Acties API that add methods for hidden endpoints.
    """

    def __init__(self, api_client: ApiClient) -> None:
        self.api_client = api_client

    @validate_call
    def publish_one_algorithm(
        self,
        organisation_id: StrictStr,
        algorithm_id: StrictStr,
        _request_timeout: (
            None
            | Annotated[StrictFloat, Field(gt=0)]
            | tuple[Annotated[StrictFloat, Field(gt=0)], Annotated[StrictFloat, Field(gt=0)]]
        ) = None,
        _request_auth: dict[StrictStr, Any] | None = None,
        _content_type: StrictStr | None = None,
        _headers: dict[StrictStr, Any] | None = None,
        _host_index: Annotated[StrictInt, Field(ge=0, le=0)] = 0,
    ) -> AlgorithmActionResponse:
        """
        Publish an algorithm (STATE_2 → PUBLISHED).

        This endpoint is hidden from the OpenAPI spec but is functional.
        It's a legacy endpoint used by ictu_last flows.

        :param organisation_id: (required)
        :type organisation_id: str
        :param algorithm_id: (required)
        :type algorithm_id: str
        :param _request_timeout: timeout setting for this request. If one
                                 number provided, it will be total request
                                 timeout. It can also be a pair (tuple) of
                                 (connection, read) timeouts.
        :type _request_timeout: int, tuple(int, int), optional
        :param _request_auth: set to override the auth_settings for an a single
                              request; this effectively ignores the
                              authentication in the spec for a single request.
        :type _request_auth: dict, optional
        :param _content_type: force content-type for the request.
        :type _content_type: str, Optional
        :param _headers: set to override the headers for a single
                         request; this effectively ignores the headers
                         in the spec for a single request.
        :type _headers: dict, optional
        :param _host_index: set to override the host_index for a single
                            request; this effectively ignores the host_index
                            in the spec for a single request.
        :type _host_index: int, optional
        :return: Returns the result object.
        """
        _param = self._publish_one_algorithm_serialize(
            organisation_id=organisation_id,
            algorithm_id=algorithm_id,
            _request_auth=_request_auth,
            _content_type=_content_type,
            _headers=_headers,
            _host_index=_host_index,
        )

        _response_types_map: dict[str, str | None] = {
            "200": "AlgorithmActionResponse",
            "401": "Message",
            "404": "Message",
            "429": "Message",
            "422": "HTTPValidationError",
        }
        response_data = self.api_client.call_api(*_param, _request_timeout=_request_timeout)  # type: ignore[reportUnknownMemberType]
        response_data.read()
        return self.api_client.response_deserialize(  # type: ignore[reportReturnType]
            response_data=response_data,
            response_types_map=_response_types_map,
        ).data

    def _publish_one_algorithm_serialize(
        self,
        organisation_id: str,
        algorithm_id: str,
        _request_auth: dict[StrictStr, Any] | None,
        _content_type: StrictStr | None,
        _headers: dict[StrictStr, Any] | None,
        _host_index: int,
    ) -> RequestSerialized:
        _host = None

        _collection_formats: dict[str, str] = {}

        _path_params: dict[str, str] = {}
        _query_params: list[tuple[str, str]] = []
        _header_params: dict[str, str | None] = _headers or {}
        _form_params: list[tuple[str, str]] = []
        _files: dict[str, str | bytes | list[str] | list[bytes] | list[tuple[str, bytes]]] = {}
        _body_params: bytes | None = None

        _path_params["organisation_id"] = organisation_id
        _path_params["algorithm_id"] = algorithm_id

        if "Accept" not in _header_params:
            _header_params["Accept"] = self.api_client.select_header_accept(["application/json"])

        _auth_settings: list[str] = ["OAuth2AuthorizationCodeBearer"]

        return self.api_client.param_serialize(  # type: ignore[reportUnknownMemberType]
            method="PUT",
            resource_path="/organizations/{organisation_id}/algorithms/{algorithm_id}/publish",
            path_params=_path_params,
            query_params=_query_params,
            header_params=_header_params,
            body=_body_params,
            post_params=_form_params,
            files=_files,
            auth_settings=_auth_settings,
            collection_formats=_collection_formats,
            _host=_host,
            _request_auth=_request_auth,
        )
