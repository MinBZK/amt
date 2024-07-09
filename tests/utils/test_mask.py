from amt.utils.mask import Mask


def test_mask_dict():
    # given
    data: dict[str | int, str] = {1: "value1", "MY_PASSWORD": "value2", "key3": "value3"}
    mask = Mask()

    # when
    masked_data = mask.secrets(data)

    # then
    assert masked_data == {1: "value1", "MY_PASSWORD": "***MASKED***", "key3": "value3"}


def test_mask_set():
    # given
    data: set[str | int] = {"value1", "password", "value3", 4}
    mask = Mask()

    # when
    masked_data = mask.secrets(data)

    # then
    assert masked_data == {"value1", "***MASKED***", "value3", 4}


def test_mask_list():
    # given
    data: list[str | int] = [1, "mysecret", "notimportant"]
    mask = Mask(mask_value="******")

    # when
    masked_data = mask.secrets(data)

    # then
    assert masked_data == [1, "******", "notimportant"]


def test_mask_string():
    # given
    data: str = "my_token"
    data_nosecret: str = "my_notimportant"
    mask = Mask(mask_keywords=["token"])

    # when
    masked_data = mask.secrets(data)
    masked_data_nosecret = mask.secrets(data_nosecret)

    # then
    assert masked_data == "***MASKED***"
    assert masked_data_nosecret == "my_notimportant"
