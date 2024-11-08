from amt.schema.group_by_category import GroupByCategory


def test_group_by_category():
    group_by_category = GroupByCategory(id="1", name="test")
    assert group_by_category.id == "1"
    assert group_by_category.name == "test"
