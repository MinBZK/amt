# TODO: fix this method
from dataclasses import dataclass

from amt.api.routes.shared import replace_none_with_empty_string_inplace
from amt.schema.shared import IterMixin


def test_replace_none_with_empty_string_inplace() -> None:
    @dataclass
    class TestClass2(IterMixin):
        test_class_obj: list[str | None] | None = None
        test_list: list[list[str | None] | None] | None = None

    @dataclass
    class TestClass(IterMixin):
        test_list: list[str | None] | None = None
        test_dict: dict[str, str | None] | None = None
        test_itermixin: IterMixin | None = None
        test_str: str | None = None

    my_obj = TestClass(
        test_list=[None],
        test_dict={"key": None, "key2": "value2"},
        test_itermixin=TestClass2(test_class_obj=[None], test_list=[["a"], ["b"], [None]]),
        test_str=None,
    )

    replace_none_with_empty_string_inplace(my_obj)

    assert my_obj.test_list == [""]
    assert my_obj.test_dict == {"key": "", "key2": "value2"}
    assert my_obj.test_str == ""
    assert my_obj.test_itermixin.test_class_obj == [""]  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportOptionalMemberAccess]
    assert my_obj.test_itermixin.test_list == [["a"], ["b"], [""]]  # pyright: ignore[reportUnknownMemberType, reportAttributeAccessIssue, reportOptionalMemberAccess]
