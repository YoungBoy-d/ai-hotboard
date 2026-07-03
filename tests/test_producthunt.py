from sources.producthunt import parse_ph


def test_parse_ph_extracts_title_link_author():
    entries = [
        {"title": "Cool App", "link": "https://producthunt.com/posts/cool",
         "author": "alice"},
        {"title": "Next Big Thing", "link": "https://producthunt.com/posts/next",
         "author": "bob"},
    ]
    items = parse_ph(entries, limit=5)
    assert [i.title for i in items] == ["Cool App", "Next Big Thing"]
    assert items[0].url == "https://producthunt.com/posts/cool"
    assert items[0].extra == "alice"


def test_parse_ph_handles_missing_fields():
    items = parse_ph([{}], limit=5)
    assert len(items) == 1
    assert items[0].title == ""
