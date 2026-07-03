import time

from sources.rss_zh import parse_rss_entry


def _entry(title, day, sub):
    return {
        "title": title,
        "link": f"https://x.com/{title}",
        "published_parsed": time.strptime(f"2026-07-{day:02d}", "%Y-%m-%d"),
        "author": sub,
    }


def test_parse_rss_entry_stamps_subsource_in_extra():
    e = _entry("AI 改变世界", 3, "少数派")
    it = parse_rss_entry(e, source="rss_zh", source_label="36氪·少数派·虎嗅",
                         sub_label="少数派")
    assert it.title == "AI 改变世界"
    assert it.url == "https://x.com/AI 改变世界"
    assert it.extra == "少数派"
    assert it.score == int(time.mktime(time.strptime("2026-07-03", "%Y-%m-%d")))


def test_parse_rss_entry_without_published():
    it = parse_rss_entry({"title": "x", "link": "u"}, source="rss_zh",
                         source_label="L", sub_label="36氪")
    assert it.score == 0  # 缺时间 → 0，排序沉底
