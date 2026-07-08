import datetime

from sources.base import Item
from dashboard import build_report, render_html


def _item(source, rank, title, extra="", summary="", tags=None, meta=""):
    return Item(source=source, source_label=source, rank=rank,
                title=title, url="https://x.com", score_label="▲ 10", extra=extra,
                summary=summary, tags=tags or [], meta=meta)


def test_build_report_shape_and_item_view():
    items_by_source = [
        ("hackernews", "Hacker News", [_item("hackernews", 1, "AI Boom")]),
    ]
    ai = {"editorial": [{"text": "要点一", "refs": []}], "items": {}}
    report = build_report(items_by_source, ai, today=datetime.date(2026, 7, 3))
    assert report["date"] == "2026-07-03"
    assert report["weekday"] == "周五"
    assert report["source_count"] == 1
    assert report["total"] == 1
    it = report["sources"][0]["items"][0]
    assert it["title"] == "AI Boom"
    assert it["key"] == "hackernews:1"
    assert it["domain"] == "x.com"
    assert report["sources"][0]["icon"]            # 源图标存在


def test_render_html_contains_key_sections_and_detail():
    items_by_source = [
        ("hackernews", "Hacker News",
         [_item("hackernews", 1, "AI Boom", summary="一句解读",
                tags=["LLM"], meta="作者·x")]),
    ]
    ai = {"editorial": [{"text": "今日要点一", "refs": ["hackernews:1"]}], "items": {}}
    report = build_report(items_by_source, ai, today=datetime.date(2026, 7, 3))
    html = render_html(report)
    assert "技术热点" in html and "AI" in html       # 标题改为 AI 技术热点
    assert "今日要点一" in html                          # AI 导语
    assert 'href="#hackernews:1"' in html              # 要点锚点跳到条目
    assert "一句解读" in html                            # summary 渲染
    assert "LLM" in html                                # tag chip 渲染
    assert "作者·x" in html                             # meta 渲染
    assert "Hacker News" in html                        # 源标签
    assert "AI Boom" in html                            # 条目标题
    assert "2026-07-03" in html                         # 日期


def test_render_html_escapes_unsafe_title():
    items_by_source = [
        ("hackernews", "Hacker News",
         [Item(source="hackernews", source_label="Hacker News", rank=1,
               title="<script>alert(1)</script>", url="https://x.com")]),
    ]
    report = build_report(items_by_source, {"editorial": [], "items": {}})
    html = render_html(report)
    assert "<script>alert(1)</script>" not in html   # must be escaped
    assert "&lt;script&gt;" in html                    # escaped form present
