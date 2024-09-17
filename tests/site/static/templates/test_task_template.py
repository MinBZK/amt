from amt.api.deps import templates
from amt.models import Task
from tests.constants import default_fastapi_request


# loading the environment
def test_template_rendering():
    # given
    request = default_fastapi_request()

    task = Task(id=1, title="Test Task", description="Test Description", sort_order=1)
    result = templates.TemplateResponse(request, "parts/task.html.j2", context={"task": task})
    expected_result = """
    <div id="card-content-1" data-id="1">
      <div class="rvo-label--sm">TestTask</div>
      <div>TestDescription</div>
    </div>
    """
    # todo (robbert) there is probably a better way to clean results than replacing newlines and spaces
    #  and we probably would want a function for it
    cleaned_results: str = result.body.decode().replace("\n", "").replace(" ", "")  # pyright: ignore [reportUnknownMemberType, reportUnknownVariableType, reportAttributeAccessIssue]
    cleaned_expected_result: str = expected_result.replace("\n", "").replace(" ", "")
    assert cleaned_results == cleaned_expected_result
