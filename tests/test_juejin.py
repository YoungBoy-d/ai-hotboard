from sources.juejin import parse_juejin


def test_parse_juejin_filters_pins_and_sorts_by_digg():
    # 2026 起 API 结构：title/article_id/digg_count 在 item_info.article_info 下
    def row(item_type, aid, title, dig):
        return {"item_type": item_type,
                "item_info": {"article_info": {"article_id": aid, "title": title, "digg_count": dig}}}

    data = {"data": [
        row(2, "a1", "低赞", 5),
        row(4, "p1", "沸点", 999),   # item_type!=2 → 沸点，过滤
        row(2, "a2", "高赞", 200),
    ]}
    items = parse_juejin(data, limit=5)
    assert [i.title for i in items] == ["高赞", "低赞"]
    assert items[0].url == "https://juejin.cn/post/a2"
    assert items[0].score_label == "👍 200"
