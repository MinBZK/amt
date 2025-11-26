import datetime
import logging
from http.client import HTTPException
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Request,
)
from fastapi.responses import HTMLResponse, RedirectResponse

from amt.algoritmeregister.auth import get_access_token
from amt.algoritmeregister.mapper import AlgorithmMapper
from amt.algoritmeregister.openapi.v1_0.client.openapi_client import AlgorithmSummary
from amt.algoritmeregister.publisher import (
    PublicationResult,
    ReleaseResult,
    get_algorithms_status,
    publish_algorithm,
    release_algorithm,
    preview_algorithm,
    PreviewResult,
)
from amt.api.decorators import permission
from amt.api.deps import templates
from amt.api.navigation import (
    BaseNavigationItem,
    Navigation,
    resolve_base_navigation_items,
)
from amt.api.publication_statuses import PublicationStatuses
from amt.api.routes.algorithm import get_algorithm_details_tabs, get_algorithm_or_error
from amt.core.authorization import (
    AuthorizationResource,
    AuthorizationVerb,
)
from amt.core.session_utils import (
    get_algoritmeregister_credentials,
    AlgoritmeregisterCredentials,
    store_algoritmeregister_credentials,
)
from amt.enums.tasks import (
    Status,
)
from amt.models import Publication
from amt.schema.algoritmeregister import AlgoritmeregisterCredentials
from amt.services.algorithms import AlgorithmsService
from amt.services.publications import PublicationsService
from amt.services.services_provider import ServicesProvider, get_service_provider

router = APIRouter()
logger = logging.getLogger(__name__)

# TODO: decide where credentials come from
username = "rig"
password = "rig"
organisation_id = "RIG"


@router.post("/{algorithm_id}/ar-login")
async def ar_login(
    request: Request,
    algorithm_id: int,
    credentials: AlgoritmeregisterCredentials,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    access_token = await get_access_token(credentials.username, credentials.password)
    credentials.token = access_token
    store_algoritmeregister_credentials(request, credentials)

    algorithms_service = await services_provider.get(AlgorithmsService)
    publication_service = await services_provider.get(PublicationsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    publication = await publication_service.get_by_algorithm_id(algorithm_id)

    publication_status = None
    if publication is not None:
        algorithm_summary: list[AlgorithmSummary] = await get_algorithms_status(
            username, password, publication.organization_code, publication.lars
        )
        if algorithm_summary[0].published:
            publication_status = PublicationStatuses.PUBLISHED
        elif algorithm_summary[0].current_version_released:
            publication_status = PublicationStatuses.STATE_2
        else:
            publication_status = PublicationStatuses.STATE_1

    context = {
        "permission_path": AuthorizationResource.ALGORITHM_SYSTEMCARD.format_map({"algorithm_id": algorithm.id}),
        "statuses": Status,
        "algorithm": algorithm,
        "publication": publication,
        "publication_status": publication_status,
        "PublicationStatuses": PublicationStatuses,
        "algorithm_id": algorithm.id,
        "base_href": f"/algorithm/{algorithm_id}/publish",
        "is_ar_logged_in": get_algoritmeregister_credentials(request) is not None,
    }

    return templates.TemplateResponse(request, "publish/parts/ar_status.html.j2", context)


# TODO: add new permission: PUBLISH
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.CREATE]})
@router.get("/{algorithm_id}/publish")
async def pre_publish(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    publication_service = await services_provider.get(PublicationsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    publication = await publication_service.get_by_algorithm_id(algorithm_id)

    publication_status = None
    if publication is not None:
        algorithm_summary: list[AlgorithmSummary] = await get_algorithms_status(
            username, password, publication.organization_code, publication.lars
        )
        if algorithm_summary[0].published:
            publication_status = PublicationStatuses.PUBLISHED
        elif algorithm_summary[0].current_version_released:
            publication_status = PublicationStatuses.STATE_2
        else:
            publication_status = PublicationStatuses.STATE_1

    tab_items = get_algorithm_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(
                custom_display_text=algorithm.name,
                url="/algorithm/{algorithm_id}/details",
            ),
            Navigation.ALGORITHM_PUBLISH,
        ],
        request,
    )

    test = get_algoritmeregister_credentials(request)
    print(test)

    context = {
        "permission_path": AuthorizationResource.ALGORITHM_SYSTEMCARD.format_map({"algorithm_id": algorithm.id}),
        "statuses": Status,
        "algorithm": algorithm,
        "publication": publication,
        "publication_status": publication_status,
        "PublicationStatuses": PublicationStatuses,
        "algorithm_id": algorithm.id,
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
        "base_href": f"/algorithm/{algorithm_id}/publish",
        "is_ar_logged_in": get_algoritmeregister_credentials(request) is not None,
    }

    return templates.TemplateResponse(request, "publish/pre_publish.html.j2", context)


# TODO: add new permission: PUBLISH
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.CREATE]})
@router.get("/{algorithm_id}/publish/start")
async def publish_start(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    publication_service = await services_provider.get(PublicationsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)

    tab_items = get_algorithm_details_tabs(request)

    breadcrumbs = resolve_base_navigation_items(
        [
            Navigation.ALGORITHMS_ROOT,
            BaseNavigationItem(
                custom_display_text=algorithm.name,
                url="/algorithm/{algorithm_id}/details",
            ),
            Navigation.ALGORITHM_PUBLISH,
        ],
        request,
    )

    publication = await publication_service.get_by_algorithm_id(algorithm_id)

    publication_model = AlgorithmMapper.to_publication_model(algorithm)
    # TODO: this is for jinja dump only
    publication_model_json = publication_model.model_dump_json(indent=2, exclude_none=True)

    create_result = None
    release_result = None
    publish_result = None
    error_message = None

    # Step 1: Create algorithm (STATE_1)
    create_result: PublicationResult = await publish_algorithm(
        algorithm=algorithm,
        username=username,
        password=password,
        organisation_id=organisation_id,
    )

    steps = [
        {"state": "start", "line": "straight", "size": "md", "label": "Start", "link": "#"},
        {"state": "incomplete", "line": "straight", "size": "md", "label": "Publicatie voorbereiden", "link": "#"},
        {"state": "incomplete", "line": "straight", "size": "md", "label": "Preview & controleren", "link": "#"},
        {"state": "incomplete", "line": "straight", "size": "md", "label": "Publiceren", "link": "#"},
        {"state": "end", "line": "none", "size": "md", "label": "Einde", "link": "#"},
    ]

    steps[1]["state"] = "doing"

    # if publication is None and create_result.lars_code:
    #     publication = Publication(
    #         last_updated=datetime.datetime.now(tz=datetime.UTC),
    #         algorithm=algorithm,
    #         lars=create_result.lars_code,
    #         organization_code=organisation_id,
    #     )
    #     await publication_service.update(publication)

    #
    #     if create_result.get("success"):
    #         lars_code = create_result.get("lars_code")
    #         logger.info(f"Algorithm created with LARS code: {lars_code}")
    #
    #         # Step 2: Release algorithm (STATE_1 → STATE_2)
    #         release_result = await release_algorithm(
    #             username=username,
    #             password=password,
    #             organisation_id=organisation_id,
    #             lars_code=lars_code,
    #         )
    #
    #         if release_result.get("success"):
    #             logger.info(f"Algorithm {lars_code} released to STATE_2")
    #
    #             # Step 3: Publish algorithm (STATE_2 → PUBLISHED)
    #             publish_result = await publish_algorithm_final(
    #                 username=username,
    #                 password=password,
    #                 organisation_id=organisation_id,
    #                 lars_code=lars_code,
    #             )
    #
    #             if publish_result.get("success"):
    #                 logger.info(f"Algorithm {lars_code} published successfully")
    #             else:
    #                 logger.error(f"Failed to publish algorithm: {publish_result.get('error')}")
    #                 error_message = publish_result.get("message")
    #         else:
    #             logger.error(f"Failed to release algorithm: {release_result.get('error')}")
    #             error_message = release_result.get("message")
    #     else:
    #         logger.error(f"Failed to create algorithm: {create_result.get('error')}")
    #         error_message = create_result.get("message")

    # except AlgoritmeregisterAuthError as e:
    #     logger.error(f"Authentication error when publishing algorithm: {e}")
    #     error_message = str(e)
    # except Exception as e:
    #     logger.error(f"Unexpected error when publishing algorithm: {e}")
    #     error_message = str(e)

    context = {
        "permission_path": AuthorizationResource.ALGORITHM_SYSTEMCARD.format_map({"algorithm_id": algorithm.id}),
        "statuses": Status,
        "algorithm": algorithm,
        "algorithm_id": algorithm.id,
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
        "publication_model": publication_model,
        "publication_model_json": publication_model_json,
        "base_href": f"/algorithm/{algorithm_id}/publish",
        "create_result": create_result,
        "release_result": release_result,
        "publish_result": publish_result,
        "error_message": error_message,
        "steps": steps,
    }

    return templates.TemplateResponse(request, "publish/publish_start.html.j2", context)


# TODO: add new permission: PUBLISH
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.CREATE]})
@router.get("/{algorithm_id}/release/{lars}")
async def publish_release(
    request: Request,
    algorithm_id: int,
    lars: str,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    publication_service = await services_provider.get(PublicationsService)

    publication = await publication_service.get_by_algorithm_id(algorithm_id)

    if publication is None:
        raise HTTPException(status_code=404, detail="Publication not found")

    await release_algorithm(username=username, password=password, organisation_id=organisation_id, lars_code=lars)

    publication.publication_status = PublicationStatuses.STATE_2
    await publication_service.update(publication)

    return templates.Redirect(
        request,
        f"/algorithm/{algorithm_id}/redirect?to=/algorithm/{algorithm_id}/publish",
    )


@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.CREATE]})
@router.get("/{algorithm_id}/preview/{lars}")
async def preview(
    request: Request,  # needed for authorization
    algorithm_id: int,
    lars: str,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> RedirectResponse:
    publication_service = await services_provider.get(PublicationsService)

    publication = await publication_service.get_by_algorithm_id(algorithm_id)

    if publication is None:
        raise HTTPException(status_code=404, detail="Publication not found")

    preview_result: PreviewResult = await preview_algorithm(
        username=username, password=password, organisation_id=organisation_id, lars_code=lars
    )

    publication.publication_status = PublicationStatuses.STATE_2
    await publication_service.update(publication)

    return RedirectResponse(url=preview_result.preview_url)
