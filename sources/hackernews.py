import requests

from config import REQUEST_HEADERS, REQUEST_TIMEOUT, is_ai_related
from sources.base import BaseFetcher, Item

HN_API = "https://hn.algolia.com/api/v1/search"


class HackerNewsFetcher(BaseFetcher):
    source = "hackernews"
    source_label = "Hacker News"

    def fetch(self, limit: int = 5) -> list[Item]:
        resp = requests.get(
            HN_API,
            params={"tags": "front_page", "hitsPerPage": 100},
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        # 取较大池按热度排序后，再按 AI 关键词过滤，保证 limit 条都与 AI 相关
        pool = parse_hn(resp.json(), limit=100, source=self.source,
                        source_label=self.source_label)
        ai = [it for it in pool if is_ai_related(it.title)]
        return ai[:limit]


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
        title = h.get("title", "") or ""
        chips = ["热议"] if comments >= 100 else []
        items.append(Item(
            source=source, source_label=source_label, rank=0,
            title=title,
            url=url,
            score=points,
            score_label=f"▲ {points} · 💬 {comments}",
            extra="",
            description="",
            tags=chips,
            meta="",
        ))
    return items
