from sources.v2ex import parse_v2ex


def test_parse_v2ex_sorts_by_replies_and_uses_node():
    topics = [
        {"title": "A", "url": "https://www.v2ex.com/t/1", "replies": 3,
         "node": {"title": "Python"}},
        {"title": "B", "url": "https://www.v2ex.com/t/2", "replies": 30,
         "node": {"title": "程序员"}},
    ]
    items = parse_v2ex(topics, limit=5)
    assert [i.title for i in items] == ["B", "A"]
    assert items[0].score_label == "💬 30"
    assert items[0].extra == "程序员"
