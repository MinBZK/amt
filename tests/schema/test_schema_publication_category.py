from amt.schema.publication_category import PublicationCategory


def test_publication_category():
    publication_category = PublicationCategory(id="1", name="test")
    assert publication_category.id == "1"
    assert publication_category.name == "test"
