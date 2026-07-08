import re
import time

import feedparser

from config import REQUEST_HEADERS, RSSHUB_BASE, is_ai_related
from sources.base import BaseFetcher, Item

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")


class AiZhFetcher(BaseFetcher):
    """中文 AI 资讯：聚合多个中文 RSS，并按 AI 关键词过滤。

    取舍：虎嗅/机器之心/量子位等都依赖 RSSHub，而公共 rsshub.app 在 CI 上长期
    返回 403/空（本项目老 payload 已验证）。因此主力用"原生直连 RSS"——CI 可靠：
    - Solidot（奇客）：原生 RSS，AI/科技内容密集
    - 少数派：原生 RSS，已验证可抓
    - 机器之心：官方 RSS（若失效自动忽略）
    量子位仍走 RSSHub，自建 RSSHUB_BASE 后自动生效。最后按 is_ai_related 过滤。
    """
    source = "ai_zh"
    source_label = "中文 AI 资讯"

    def _feeds(self) -> list[tuple[str, str]]:
        return [
            # 原生直连 RSS（不依赖 RSSHub，CI 可靠）
            ("Solidot", "https://www.solidot.org/index.rss"),
            ("少数派", "https://sspai.com/feed"),
            ("机器之心", "https://www.jiqizhixin.com/rss"),
            # 经 RSSHub：公共实例常空，自建并设 RSSHUB_BASE 后启用
            ("量子位", f"{RSSHUB_BASE}/qbitai"),
        ]

    def fetch(self, limit: int = 5) -> list[Item]:
        all_items: list[Item] = []
        for sub_label, url in self._feeds():
            d = feedparser.parse(url, request_headers=REQUEST_HEADERS)
            for e in d.entries:
                it = parse_ai_entry(e, self.source, self.source_label, sub_label)
                # 只保留与 AI 相关的条目
                if is_ai_related(f"{it.title} {it.description}"):
                    all_items.append(it)
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
