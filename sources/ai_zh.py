import re
import time

import feedparser

from config import REQUEST_HEADERS, RSSHUB_BASE
from sources.base import BaseFetcher, Item

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


class AiZhFetcher(BaseFetcher):
    """中文 AI 媒体（机器之心 / 量子位），经 RSSHub 订阅。

    路由依赖 RSSHUB_BASE；公共实例可能无数据，空源由 safe_fetch 兜底。
    """
    source = "ai_zh"
    source_label = "机器之心·量子位"

    def _feeds(self) -> list[tuple[str, str]]:
        return [
            ("机器之心", f"{RSSHUB_BASE}/jiqizhixin/news"),
            ("量子位", f"{RSSHUB_BASE}/qbitai/articles"),
        ]

    def fetch(self, limit: int = 5) -> list[Item]:
        all_items: list[Item] = []
        for sub_label, url in self._feeds():
            d = feedparser.parse(url, request_headers=REQUEST_HEADERS)
            for e in d.entries:
                all_items.append(parse_ai_entry(
                    e, self.source, self.source_label, sub_label))
        # 按发布时间倒序，取最新 limit 条
        all_items.sort(key=lambda it: it.score, reverse=True)
        return all_items[:limit]


def _strip(text: str) -> str:
    return _WS.sub(" ", _TAG.sub("", text or "")).strip()


def parse_ai_entry(entry, source: str, source_label: str, sub_label: str) -> Item:
    published = entry.get("published_parsed")
    ts = int(time.mktime(published)) if published else 0
    date = time.strftime("%Y-%m-%d", published) if published else ""
    summary = _strip(entry.get("summary", ""))[:200]
    return Item(
        source=source, source_label=source_label, rank=0,
        title=entry.get("title", "") or "",
        url=entry.get("link", "") or "",
        score=ts,
        score_label="",
        extra=sub_label,
        description=summary,
        tags=[sub_label],
        meta=f"📅 {date}" if date else "",
    )
