import requests

from config import REQUEST_HEADERS, REQUEST_TIMEOUT, is_ai_related
from sources.base import BaseFetcher, Item

JUEJIN_API = "https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed"


class JuejinFetcher(BaseFetcher):
    source = "juejin"
    source_label = "掘金 AI"

    def fetch(self, limit: int = 5) -> list[Item]:
        resp = requests.post(
            JUEJIN_API,
            json={"id_type": 2, "sort_type": 200, "cursor": "0",
                  "limit": 40},  # 拉大池子便于 AI 关键词过滤
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        pool = parse_juejin(resp.json(), limit=40, source=self.source,
                            source_label=self.source_label)
        ai = [it for it in pool if is_ai_related(f"{it.title} {it.description}")]
        return ai[:limit]


def parse_juejin(data: dict, limit: int = 5,
                 source: str = "juejin", source_label: str = "掘金 AI") -> list[Item]:
    rows = data.get("data", []) or []
    rows = [r for r in rows if r.get("item_type", 2) == 2]  # 仅文章，过滤沸点

    # 2026 起 API 结构变更：title/article_id/digg_count 嵌套在 item_info.article_info 下
    def _article(row: dict) -> dict:
        return (row.get("item_info") or {}).get("article_info") or {}

    rows = sorted(rows, key=lambda r: _article(r).get("digg_count", 0) or 0, reverse=True)
    items: list[Item] = []
    for r in rows[:limit]:
        info = _article(r)
        aid = info.get("article_id", "")
        dig = info.get("digg_count", 0) or 0
        title = info.get("title", "") or ""
        brief = (info.get("brief_content", "") or "").strip()[:200]

        category = r.get("category") or {}
        cat_name = category.get("category_name", "") if isinstance(category, dict) else ""

        chips = [cat_name] if cat_name else []
        items.append(Item(
            source=source, source_label=source_label, rank=0,
            title=title,
            url=f"https://juejin.cn/post/{aid}",
            score=dig,
            score_label=f"👍 {dig}",
            extra="",
            description=brief,
            tags=chips,
            meta="",
        ))
    return items
