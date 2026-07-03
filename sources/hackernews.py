import requests

from config import REQUEST_HEADERS, REQUEST_TIMEOUT
from sources.base import BaseFetcher, Item

HN_API = "https://hn.algolia.com/api/v1/search"


class HackerNewsFetcher(BaseFetcher):
    source = "hackernews"
    source_label = "Hacker News"

    def fetch(self, limit: int = 5) -> list[Item]:
        resp = requests.get(
            HN_API,
            params={"tags": "front_page", "hitsPerPage": 50},
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return parse_hn(resp.json(), limit, self.source, self.source_label)


def parse_hn(data: dict, limit: int = 5,
             source: str = "hackernews", source_label: str = "Hacker News") -> list[Item]:
    hits = data.get("hits", [])
    hits = sorted(hits, key=lambda h: h.get("points", 0) or 0, reverse=True)
    items: list[Item] = []
    for h in hits[:limit]:
        oid = h.get("objectID", "")
        url = h.get("url") or f"https://news.ycombinator.com/item?id={oid}"
        points = h.get("points", 0) or 0
        comments = h.get("num_comments", 0) or 0
        items.append(Item(
            source=source, source_label=source_label, rank=0,
            title=h.get("title", "") or "",
            url=url,
            score=points,
            score_label=f"▲ {points}",
            extra=f"{comments} 评论",
        ))
    return items
