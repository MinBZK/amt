from amt.models.user import User


def test_model_basic_user():
    # given

    user = User(id="70419b8d-29ff-4c51-9822-05a46f6c916e", name="Test user")

    # then
    assert user.id == "70419b8d-29ff-4c51-9822-05a46f6c916e"
    assert user.name == "Test user"
