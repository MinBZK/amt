import datetime
import logging
import re
from typing import Annotated

from fastapi import (
    APIRouter,
    Depends,
    Request,
)
from fastapi.responses import HTMLResponse, RedirectResponse
from pydantic import ValidationError

from amt.algoritmeregister.auth import AlgoritmeregisterAuthError, get_access_token
from amt.algoritmeregister.mapper import AlgorithmMapper
from amt.algoritmeregister.openapi.base import OrganisationApi
from amt.algoritmeregister.openapi.v1_0.client.openapi_client import AlgorithmSummary, ApiClient, Configuration
from amt.algoritmeregister.publisher import (
    PreviewResult,
    PublicationResult,
    get_algorithms_status,
    preview_algorithm,
    publish_algorithm,
    release_algorithm,
    update_algorithm,
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
from amt.core.config import get_settings
from amt.core.exception_handlers import translate_pydantic_exception
from amt.core.exceptions import AMTNotFound
from amt.core.internationalization import get_current_translation
from amt.core.session_utils import (
    PublishStep,
    get_algoritmeregister_credentials,
    get_algoritmeregister_credentials_or_trigger_redirect,
    get_publish_step,
    set_publish_step,
    store_algoritmeregister_credentials,
)
from amt.models import Publication
from amt.schema.algoritmeregister import AlgoritmeregisterCredentials, OrganisationOption, OrganizationSelection
from amt.services.algorithms import AlgorithmsService
from amt.services.publications import PublicationsService
from amt.services.services_provider import ServicesProvider, get_service_provider

router = APIRouter()
logger = logging.getLogger(__name__)


def get_global_steps() -> list[dict[str, str]]:
    steps_global = [
        {"state": "start", "line": "straight", "size": "md", "label": "Start", "link": "#"},
        {
            "state": "incomplete",
            "line": "straight",
            "size": "md",
            "label": "Publicatie voorbereiden",
            "link": "./prepare",
        },
        {
            "state": "incomplete",
            "line": "straight",
            "size": "md",
            "label": "Preview & controleren",
            "link": "./preview",
        },
        {"state": "incomplete", "line": "straight", "size": "md", "label": "Publiceren", "link": "./confirm"},
        {"state": "end", "line": "none", "size": "md", "label": "Einde", "link": "#"},
    ]
    return steps_global


def set_step_state(steps: list[dict[str, str]], link: str, state: str) -> None:
    """Set the state of a step by its link URL."""
    for step in steps:
        if step["link"] == link:
            step["state"] = state
            return


def set_steps_completed_until(steps: list[dict[str, str]], current_link: str) -> None:
    """Mark all steps as completed up to (but not including) the given link,
    and mark the step with the given link as 'doing'."""
    for step in steps:
        if step["link"] == current_link:
            step["state"] = "doing"
            return
        if step["state"] not in ("start", "end"):
            step["state"] = "completed"


def get_publication_url(organization_code: str, lars: str, name: str) -> str:
    """Create the public URL for a published algorithm.

    URL format: {base_url}/nl/algoritme/{organization_code}/{lars}/{slug}
    where slug is the algorithm name in lowercase with spaces replaced by hyphens.
    """
    slug = re.sub(r"[^a-z0-9\-]", "", name.lower().replace(" ", "-"))
    settings = get_settings()
    return f"{settings.ALGORITMEREGISTER_URL}/nl/algoritme/{organization_code}/{lars}/{slug}"


@router.post("/{algorithm_id}/publish/login")
async def ar_login(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    body = await request.json()

    errors: dict[str, str] = {}
    try:
        credentials = AlgoritmeregisterCredentials.model_validate(body)
    except ValidationError as e:
        translations = get_current_translation(request)
        for error in e.errors():
            field_name = str(error["loc"][0])
            errors[field_name] = translate_pydantic_exception(dict(error), translations)

        return templates.TemplateResponse(
            request,
            "publish/parts/ar_login_form.html.j2",
            {
                "errors": errors,
                "values": body,
            },
        )

    try:
        access_token = await get_access_token(credentials.username, credentials.password)
    except AlgoritmeregisterAuthError:
        return templates.TemplateResponse(
            request,
            "publish/parts/ar_login_form.html.j2",
            {
                "values": body,
                "login_error": True,
            },
        )

    credentials.token = access_token

    settings = get_settings()
    configuration = Configuration(host=settings.ALGORITMEREGISTER_BASE_API_URL, access_token=access_token)
    configuration.verify_ssl = settings.VERIFY_SSL
    api_client = ApiClient(configuration)
    org_api = OrganisationApi(api_client)

    try:
        org_response = org_api.get_all()
        credentials.organisations = [
            OrganisationOption(value=org.org_id, label=org.name) for org in org_response.organisations
        ]
        if len(credentials.organisations) == 1:
            credentials.organization_id = credentials.organisations[0].value
    except Exception:
        logger.exception("Failed to fetch organisations from Algoritmeregister")

    store_algoritmeregister_credentials(request, credentials)

    publication_service = await services_provider.get(PublicationsService)
    publication = await publication_service.get_by_algorithm_id(algorithm_id)

    if not publication:
        set_publish_step(request, algorithm_id, PublishStep.PREPARE)

    org_context = get_organization_selector_context(credentials)

    return templates.TemplateResponse(
        request,
        "publish/parts/ar_login_success.html.j2",
        {
            "algorithm_id": algorithm_id,
            **org_context,
        },
    )


def get_organization_name(credentials: AlgoritmeregisterCredentials) -> str | None:
    """Get the organization name from credentials based on the selected organization_id."""
    if not credentials.organization_id:
        return None
    for org in credentials.organisations:
        if org.value == credentials.organization_id:
            return org.label
    return credentials.organization_id


def get_organization_selector_context(
    credentials: AlgoritmeregisterCredentials | None,
    errors: dict[str, str] | None = None,
    force_select: bool = False,
) -> dict[str, object]:
    """Build context for the organization selector partial."""
    if credentials is None:
        return {"organisations": [], "selected_org_id": None, "selected_org_name": None, "errors": errors or {}}

    selected_org_id = None if force_select else credentials.organization_id
    selected_org_name = None
    if selected_org_id:
        for org in credentials.organisations:
            if org.value == selected_org_id:
                selected_org_name = org.label
                break

    return {
        "organisations": [{"value": org.value, "label": org.label} for org in credentials.organisations],
        "selected_org_id": selected_org_id,
        "selected_org_name": selected_org_name,
        "errors": errors or {},
    }


@router.get("/{algorithm_id}/publish/organization-selector")
async def get_organization_selector(
    request: Request,
    algorithm_id: int,
    select: bool = False,
) -> HTMLResponse:
    credentials = get_algoritmeregister_credentials(request)
    context = get_organization_selector_context(credentials, force_select=select)
    return templates.TemplateResponse(request, "publish/parts/ar_organization_selector.html.j2", context)


@router.post("/{algorithm_id}/publish/set-organization", response_model=None)
async def ar_set_organization(
    request: Request,
    algorithm_id: int,
) -> HTMLResponse | RedirectResponse:
    body = await request.json()

    credentials = get_algoritmeregister_credentials(request)

    try:
        selection = OrganizationSelection.model_validate(body)
    except ValidationError as e:
        translations = get_current_translation(request)
        errors: dict[str, str] = {}
        for error in e.errors():
            field_name = str(error["loc"][0])
            errors[field_name] = translate_pydantic_exception(dict(error), translations)

        context = get_organization_selector_context(credentials, errors=errors)
        return templates.TemplateResponse(request, "publish/parts/ar_organization_selector.html.j2", context)

    if credentials is None:
        return templates.Redirect(request, f"/algorithm/{algorithm_id}/publish/connection")

    credentials.organization_id = selection.organization_id

    if selection.organization_name:
        credentials.organisations = [
            OrganisationOption(value=selection.organization_id, label=selection.organization_name)
        ]

    store_algoritmeregister_credentials(request, credentials)

    return templates.Redirect(request, f"/algorithm/{algorithm_id}/publish/connection")


@router.get("/{algorithm_id}/publish", response_model=None)
@permission({AuthorizationResource.ALGORITHM: [AuthorizationVerb.CREATE]})
async def publish_router(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse | RedirectResponse:
    publication_service = await services_provider.get(PublicationsService)
    publication = await publication_service.get_by_algorithm_id(algorithm_id)

    current_step = get_publish_step(request, algorithm_id)
    if current_step is None and publication is None:
        url = f"/algorithm/{algorithm_id}/publish/explanation"
    elif current_step is not None:
        url = f"/algorithm/{algorithm_id}/publish/{current_step.value}"
    else:
        url = f"/algorithm/{algorithm_id}/publish/status"
    return RedirectResponse(
        url=url,
        status_code=302,
    )


@router.get("/{algorithm_id}/publish/explanation", response_model=None)
@permission({AuthorizationResource.ALGORITHM_PUBLISH: [AuthorizationVerb.CREATE]})
async def publication_explanation(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse | RedirectResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)

    tab_items = get_algorithm_details_tabs(request, False)

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

    context = {
        "algorithm": algorithm,
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
        "is_ar_logged_in": get_algoritmeregister_credentials(request) is not None,
    }

    return templates.TemplateResponse(request, "publish/publish_explanation.html.j2", context)


@router.get("/{algorithm_id}/publish/status", response_model=None)
@permission({AuthorizationResource.ALGORITHM_PUBLISH: [AuthorizationVerb.CREATE]})
async def publication_status(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    get_algoritmeregister_credentials_or_trigger_redirect(request, algorithm_id)

    algorithms_service = await services_provider.get(AlgorithmsService)
    publication_service = await services_provider.get(PublicationsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    publication = await publication_service.get_by_algorithm_id(algorithm_id)

    credentials = get_algoritmeregister_credentials(request)

    current_publication_status: PublicationStatuses = PublicationStatuses.NONE
    algorithm_summary: list[AlgorithmSummary] = []
    publication_missing_in_register = False
    if publication is not None and credentials is not None:
        algorithm_summary = await get_algorithms_status(
            credentials.username, credentials.password, publication.organization_code, publication.lars
        )
        if len(algorithm_summary) == 0:
            publication_missing_in_register = True
            publication = None
            await publication_service.delete_by_algorithm_id(algorithm_id)
        else:
            if algorithm_summary[0].published:
                current_publication_status = PublicationStatuses.PUBLISHED
            elif algorithm_summary[0].current_version_released:
                current_publication_status = PublicationStatuses.STATE_2
            else:
                current_publication_status = PublicationStatuses.STATE_1

    tab_items = get_algorithm_details_tabs(request, False)

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

    publication_url = None
    if (
        current_publication_status == PublicationStatuses.PUBLISHED
        and publication is not None
        and publication.lars is not None
    ):
        publication_url = get_publication_url(publication.organization_code, publication.lars, algorithm.name)

    context = {
        "algorithm": algorithm,
        "publication": publication,
        "publication_status": current_publication_status,
        "publication_url": publication_url,
        "PublicationStatuses": PublicationStatuses,
        "algorithm_summary": algorithm_summary[0] if algorithm_summary else None,
        "publication_missing_in_register": publication_missing_in_register,
        "algorithm_id": algorithm.id,
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
    }

    return templates.TemplateResponse(request, "publish/publish_status.html.j2", context)


@router.get("/{algorithm_id}/publish/connection")
@permission({AuthorizationResource.ALGORITHM_PUBLISH: [AuthorizationVerb.CREATE]})
async def publish_connection(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    algorithms_service = await services_provider.get(AlgorithmsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)

    tab_items = get_algorithm_details_tabs(request, False)

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

    credentials = get_algoritmeregister_credentials(request)
    is_ar_logged_in = credentials is not None

    org_context = get_organization_selector_context(credentials)

    context = {
        "algorithm": algorithm,
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
        "is_ar_logged_in": is_ar_logged_in,
        **org_context,
    }

    return templates.TemplateResponse(request, "publish/publish_connection.html.j2", context)


@router.get("/{algorithm_id}/publish/prepare", response_model=None)
@permission({AuthorizationResource.ALGORITHM_PUBLISH: [AuthorizationVerb.CREATE]})
async def publish_prepare(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    get_algoritmeregister_credentials_or_trigger_redirect(request, algorithm_id)

    set_publish_step(request, algorithm_id, PublishStep.PREPARE)

    algorithms_service = await services_provider.get(AlgorithmsService)
    publication_service = await services_provider.get(PublicationsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)
    publication = await publication_service.get_by_algorithm_id(algorithm_id)

    tab_items = get_algorithm_details_tabs(request, False)

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

    steps = get_global_steps()
    set_steps_completed_until(steps, "./prepare")

    context = {
        "algorithm": algorithm,
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
        "steps": steps,
        "has_publication": publication is not None,
    }

    return templates.TemplateResponse(request, "publish/publish_prepare.html.j2", context)


@router.get("/{algorithm_id}/publish/preview", response_model=None)
@permission({AuthorizationResource.ALGORITHM_PUBLISH: [AuthorizationVerb.CREATE]})
async def publish_preview(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    select: bool = False,
) -> HTMLResponse:
    credentials = get_algoritmeregister_credentials_or_trigger_redirect(request, algorithm_id)

    set_publish_step(request, algorithm_id, PublishStep.PREVIEW)

    algorithms_service = await services_provider.get(AlgorithmsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)

    tab_items = get_algorithm_details_tabs(request, False)

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

    organization_name = get_organization_name(credentials)
    if organization_name is None:
        raise AMTNotFound()

    publication_model = AlgorithmMapper.to_publication_model(algorithm, organization_name)

    steps = get_global_steps()
    set_steps_completed_until(steps, "./preview")

    org_selector_context = get_organization_selector_context(credentials, force_select=select)

    context: dict[str, object] = {
        "algorithm": algorithm,
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
        "publication_model": publication_model,
        "steps": steps,
    }
    context.update(org_selector_context)

    return templates.TemplateResponse(request, "publish/publish_preview.html.j2", context)


@router.get("/{algorithm_id}/publish/confirm", response_model=None)
@permission({AuthorizationResource.ALGORITHM_PUBLISH: [AuthorizationVerb.CREATE]})
async def publish_confirm(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse | RedirectResponse:
    credentials = get_algoritmeregister_credentials_or_trigger_redirect(request, algorithm_id)

    if not credentials.organization_id:
        return RedirectResponse(url=f"/algorithm/{algorithm_id}/publish/preview?select=true", status_code=302)

    set_publish_step(request, algorithm_id, PublishStep.CONFIRM)

    algorithms_service = await services_provider.get(AlgorithmsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)

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

    tab_items = get_algorithm_details_tabs(request, False)

    steps = get_global_steps()
    set_steps_completed_until(steps, "/confirm")

    context = {
        "algorithm": algorithm,
        "breadcrumbs": breadcrumbs,
        "tab_items": tab_items,
        "steps": steps,
    }

    return templates.TemplateResponse(request, "publish/publish_confirm.html.j2", context)


@router.get("/{algorithm_id}/publish/send", response_model=None)
@permission({AuthorizationResource.ALGORITHM_PUBLISH: [AuthorizationVerb.CREATE]})
async def publish_send(
    request: Request,
    algorithm_id: int,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
    release: bool = False,
) -> HTMLResponse:
    credentials = get_algoritmeregister_credentials_or_trigger_redirect(request, algorithm_id)

    algorithms_service = await services_provider.get(AlgorithmsService)
    publication_service = await services_provider.get(PublicationsService)
    algorithm = await get_algorithm_or_error(algorithm_id, algorithms_service, request)

    publication = await publication_service.get_by_algorithm_id(algorithm_id)

    organization_name = get_organization_name(credentials)
    if credentials.organization_id is None or organization_name is None:
        raise AMTNotFound()

    if not publication or not publication.lars:
        create_result: PublicationResult = await publish_algorithm(
            algorithm=algorithm,
            username=credentials.username,
            password=credentials.password,
            organisation_id=credentials.organization_id,
            organisation_name=organization_name,
        )
    else:
        create_result: PublicationResult = await update_algorithm(
            algorithm=algorithm,
            username=credentials.username,
            password=credentials.password,
            organisation_id=credentials.organization_id,
            organisation_name=organization_name,
            algorithm_id=publication.lars if publication else "",
        )

    if create_result.lars_code:
        if publication is None:
            publication = Publication(
                # Using naive datetime because the database column is TIMESTAMP WITHOUT TIME ZONE
                # TODO: migrate database to TIMESTAMP WITH TIME ZONE for proper timezone handling
                last_updated=datetime.datetime.now(tz=None),  # noqa: DTZ005
                algorithm=algorithm,
                lars=create_result.lars_code,
                organization_code=credentials.organization_id,
            )
        else:
            publication.last_updated = datetime.datetime.now(tz=None)  # noqa: DTZ005
        await publication_service.update(publication)

        if release:
            await release_algorithm(
                username=credentials.username,
                password=credentials.password,
                organisation_id=credentials.organization_id,
                lars_code=create_result.lars_code,
            )
            publication.publication_status = PublicationStatuses.STATE_2
            await publication_service.update(publication)

    set_publish_step(request, algorithm_id, PublishStep.STATUS)

    return templates.Redirect(
        request, f"/algorithm/{algorithm_id}/redirect?to=/algorithm/{algorithm_id}/publish/status"
    )


@router.get("/{algorithm_id}/release/{lars}")
@permission({AuthorizationResource.ALGORITHM_PUBLISH: [AuthorizationVerb.CREATE]})
async def publish_release(
    request: Request,
    algorithm_id: int,
    lars: str,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> HTMLResponse:
    credentials = get_algoritmeregister_credentials_or_trigger_redirect(request, algorithm_id)

    publication_service = await services_provider.get(PublicationsService)
    publication = await publication_service.get_by_algorithm_id(algorithm_id)

    if not publication or credentials.organization_id is None:
        raise AMTNotFound()

    await release_algorithm(
        username=credentials.username,
        password=credentials.password,
        organisation_id=credentials.organization_id,
        lars_code=lars,
    )

    publication.publication_status = PublicationStatuses.STATE_2
    await publication_service.update(publication)

    return templates.Redirect(
        request,
        f"/algorithm/{algorithm_id}/redirect?to=/algorithm/{algorithm_id}/publish/status",
    )


@permission({AuthorizationResource.ALGORITHM_PUBLISH: [AuthorizationVerb.CREATE]})
@router.get("/{algorithm_id}/preview/{lars}")
async def preview(
    request: Request,  # needed for authorization
    algorithm_id: int,
    lars: str,
    services_provider: Annotated[ServicesProvider, Depends(get_service_provider)],
) -> RedirectResponse:
    credentials = get_algoritmeregister_credentials_or_trigger_redirect(request, algorithm_id)

    publication_service = await services_provider.get(PublicationsService)
    publication = await publication_service.get_by_algorithm_id(algorithm_id)

    if publication is None or credentials.organization_id is None:
        raise AMTNotFound()

    preview_result: PreviewResult = await preview_algorithm(
        username=credentials.username,
        password=credentials.password,
        organisation_id=credentials.organization_id,
        lars_code=lars,
    )

    publication.publication_status = PublicationStatuses.STATE_2
    await publication_service.update(publication)

    return RedirectResponse(url=preview_result.preview_url)
