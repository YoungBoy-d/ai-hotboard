import requests

from config import REQUEST_HEADERS, REQUEST_TIMEOUT
from sources.base import BaseFetcher, Item

V2EX_API = "https://www.v2ex.com/api/topics/hot.json"


class V2EXFetcher(BaseFetcher):
    source = "v2ex"
    source_label = "V2EX"

    def fetch(self, limit: int = 5) -> list[Item]:
        resp = requests.get(V2EX_API, headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        return parse_v2ex(resp.json(), limit, self.source, self.source_label)


def parse_v2ex(topics: list, limit: int = 5,
               source: str = "v2ex", source_label: str = "V2EX") -> list[Item]:
    topics = sorted(topics, key=lambda t: t.get("replies", 0) or 0, reverse=True)
    items: list[Item] = []
    for t in topics[:limit]:
        node = t.get("node") or {}
        node_title = node.get("title", "") if isinstance(node, dict) else ""
        replies = t.get("replies", 0) or 0
        items.append(Item(
            source=source, source_label=source_label, rank=0,
            title=t.get("title", "") or "",
            url=t.get("url", "") or "",
            score=replies,
            score_label=f"💬 {replies}",
            extra=node_title,
        ))
    return items
