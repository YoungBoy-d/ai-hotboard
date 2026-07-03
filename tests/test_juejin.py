from sources.juejin import parse_juejin


def test_parse_juejin_filters_pins_and_sorts_by_digg():
    data = {
        "data": [
            {"item_type": 2, "article_info": {"article_id": "a1", "title": "低赞"},
             "content_counter": {"dig_count": 5}},
            {"item_type": 4, "article_info": {"article_id": "p1", "title": "沸点"},
             "content_counter": {"dig_count": 999}},  # item_type!=2 → 沸点，过滤
            {"item_type": 2, "article_info": {"article_id": "a2", "title": "高赞"},
             "content_counter": {"dig_count": 200}},
        ]
    }
    items = parse_juejin(data, limit=5)
    assert [i.title for i in items] == ["高赞", "低赞"]
    assert items[0].url == "https://juejin.cn/post/a2"
    assert items[0].score_label == "👍 200"
