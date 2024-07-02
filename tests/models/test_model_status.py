from tad.models.status import Status


def test_model_basic_status():
    # given
    status = Status(name="Test status", sort_order=1.0)

    # then
    assert status.name == "Test status"
    assert status.sort_order == 1.0
