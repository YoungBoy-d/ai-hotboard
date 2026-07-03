import time

import feedparser

from config import REQUEST_HEADERS, RSSHUB_BASE
from sources.base import BaseFetcher, Item

SSPAI_FEED = "https://sspai.com/feed"


class RssZhFetcher(BaseFetcher):
    source = "rss_zh"
    source_label = "36氪·少数派·虎嗅"

    def _feeds(self) -> list[tuple[str, str]]:
        return [
            ("少数派", SSPAI_FEED),
            ("36氪", f"{RSSHUB_BASE}/36kr/newsflashes"),
            ("虎嗅", f"{RSSHUB_BASE}/huxiu/article"),
        ]

    def fetch(self, limit: int = 5) -> list[Item]:
        all_items: list[Item] = []
        for sub_label, url in self._feeds():
            d = feedparser.parse(url, request_headers=REQUEST_HEADERS)
            for e in d.entries:
                all_items.append(parse_rss_entry(
                    e, self.source, self.source_label, sub_label))
        # 按发布时间倒序，取最新 limit 条
        all_items.sort(key=lambda it: it.score, reverse=True)
        return all_items[:limit]


def parse_rss_entry(entry, source: str, source_label: str, sub_label: str) -> Item:
    published = entry.get("published_parsed")
    ts = int(time.mktime(published)) if published else 0
    return Item(
        source=source, source_label=source_label, rank=0,
        title=entry.get("title", "") or "",
        url=entry.get("link", "") or "",
        score=ts,
        score_label="",
        extra=sub_label,
    )
