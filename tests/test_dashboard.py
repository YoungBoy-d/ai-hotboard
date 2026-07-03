import datetime

from sources.base import Item
from dashboard import build_report, render_html


def _item(source, rank, title, extra=""):
    return Item(source=source, source_label=source, rank=rank,
                title=title, url="https://x.com", score_label="▲ 10", extra=extra)


def test_build_report_shape():
    items_by_source = [
        ("hackernews", "Hacker News", [_item("hackernews", 1, "AI Boom")]),
    ]
    ai = {"editorial": [{"text": "要点一", "refs": []}], "translations": {}}
    report = build_report(items_by_source, ai, today=datetime.date(2026, 7, 3))
    assert report["date"] == "2026-07-03"
    assert report["weekday"] == "周五"
    assert report["source_count"] == 1
    assert report["total"] == 1
    assert report["sources"][0]["items"][0]["title"] == "AI Boom"


def test_render_html_contains_key_sections():
    items_by_source = [
        ("hackernews", "Hacker News", [_item("hackernews", 1, "AI Boom")]),
    ]
    ai = {"editorial": [{"text": "今日要点一", "refs": []}], "translations": {}}
    report = build_report(items_by_source, ai, today=datetime.date(2026, 7, 3))
    html = render_html(report)
    assert "科技" in html and "AI" in html              # 标题
    assert "今日要点一" in html                          # AI 导语
    assert "Hacker News" in html                        # 源标签
    assert "AI Boom" in html                            # 条目标题
    assert "2026-07-03" in html                         # 日期
