import time

from sources.ai_zh import parse_ai_entry, _strip


def test_strip_removes_html_tags():
    assert _strip("<p>hello <b>world</b></p>") == "hello world"


def test_parse_ai_entry_stamps_subsource_and_summary():
    e = {
        "title": "GPT-5 发布",
        "link": "https://www.jiqizhixin.com/article/1",
        "summary": "<p>OpenAI 发布新一代模型。</p>",
        "published_parsed": time.strptime("2026-07-03", "%Y-%m-%d"),
    }
    it = parse_ai_entry(e, source="ai_zh", source_label="机器之心·量子位",
                        sub_label="机器之心")
    assert it.title == "GPT-5 发布"
    assert it.url == "https://www.jiqizhixin.com/article/1"
    assert it.extra == "机器之心"
    assert "机器之心" in it.tags
    assert "OpenAI" in it.description        # summary 去标签后保留
    assert it.score == int(time.mktime(time.strptime("2026-07-03", "%Y-%m-%d")))
    assert "2026-07-03" in it.meta
    assert it.score_label == ""               # 资讯源无热度指标


def test_parse_ai_entry_without_published():
    it = parse_ai_entry({"title": "x", "link": "u"}, source="ai_zh",
                        source_label="L", sub_label="量子位")
    assert it.score == 0                      # 缺时间 → 排序沉底
    assert it.meta == ""
