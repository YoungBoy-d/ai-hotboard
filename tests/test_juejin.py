from sources.juejin import parse_juejin


def test_parse_juejin_filters_pins_sorts_and_extracts_brief():
    # 2026 起 API 结构：title/article_id/digg_count/brief_content 在 item_info.article_info 下
    def row(item_type, aid, title, dig, brief="", cat=""):
        return {"item_type": item_type,
                "item_info": {"article_info": {
                    "article_id": aid, "title": title,
                    "digg_count": dig, "brief_content": brief}},
                "category": {"category_name": cat}}

    data = {"data": [
        row(2, "a1", "低赞", 5),
        row(4, "p1", "沸点", 999),   # item_type!=2 → 沸点，过滤
        row(2, "a2", "高赞 AI 教程", 200, brief="讲大模型实践", cat="人工智能"),
    ]}
    items = parse_juejin(data, limit=5)
    assert [i.title for i in items] == ["高赞 AI 教程", "低赞"]
    assert items[0].url == "https://juejin.cn/post/a2"
    assert items[0].score_label == "👍 200"
    assert items[0].description == "讲大模型实践"   # 新增：摘要
    assert items[0].extra == ""
    assert "人工智能" in items[0].tags               # 分类作为标签
