from sources.hackernews import parse_hn


def test_parse_hn_sorts_by_points_and_falls_back_url():
    data = {
        "hits": [
            {"objectID": "1", "title": "Low", "points": 10, "num_comments": 1,
             "url": "https://ext.com/1"},
            {"objectID": "2", "title": "High", "points": 500, "num_comments": 42,
             "url": None},  # Ask HN 无 url → 回退 HN 讨论页
            {"objectID": "3", "title": "Mid", "points": 100, "num_comments": 5,
             "url": "https://ext.com/3"},
        ]
    }
    items = parse_hn(data, limit=5)
    assert [i.title for i in items] == ["High", "Mid", "Low"]   # 按 points 降序
    assert items[0].score_label == "▲ 500"
    assert items[0].url == "https://news.ycombinator.com/item?id=2"  # 回退
    assert items[1].url == "https://ext.com/3"
    assert items[0].extra == "42 评论"
