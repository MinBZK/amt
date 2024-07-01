from jinja2 import Environment, FileSystemLoader
from tad.models import Task

# loading the environment
env = Environment(loader=FileSystemLoader("tad/site/templates/"), autoescape=True)


def test_template_rendering():
    task = Task(id=1, title="Test Task", description="Test Description", sort_order=1)
    result = env.get_template(name="task.html.jinja").render(task=task)
    expected_result = """
    <div class="progress_card_container" id="card-1" data-id="1">
        <h4 class="margin-bottom--extra-small">Test Task</h4>
        <div>Test Description</div>
    </div>
    """
    # todo (robbert) there is probably a better way to clean results than replacing newlines and spaces
    #  and we probably would want a function for it
    cleaned_results = result.replace("\n", "").replace(" ", "")
    cleaned_expected_result = expected_result.replace("\n", "").replace(" ", "")
    assert cleaned_results == cleaned_expected_result
