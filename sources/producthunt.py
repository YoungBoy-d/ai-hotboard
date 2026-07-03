import feedparser

from config import REQUEST_HEADERS, RSSHUB_BASE
from sources.base import BaseFetcher, Item


class ProductHuntFetcher(BaseFetcher):
    source = "producthunt"
    source_label = "Product Hunt"

    def fetch(self, limit: int = 5) -> list[Item]:
        url = f"{RSSHUB_BASE}/producthunt/today"
        d = feedparser.parse(url, request_headers=REQUEST_HEADERS)
        return parse_ph(d.entries, limit, self.source, self.source_label)


def parse_ph(entries: list, limit: int = 5,
             source: str = "producthunt",
             source_label: str = "Product Hunt") -> list[Item]:
    items: list[Item] = []
    for e in entries[:limit]:
        items.append(Item(
            source=source, source_label=source_label, rank=0,
            title=e.get("title", "") or "",
            url=e.get("link", "") or "",
            score=0,
            score_label="",
            extra=e.get("author", "") or "",
        ))
    return items
