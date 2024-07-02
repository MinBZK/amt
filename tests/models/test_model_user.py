from tad.models.user import User


def test_model_basic_user():
    # given

    user = User(name="Test user", avatar=None)

    # then
    assert user.name == "Test user"
