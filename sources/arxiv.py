import re
import time

import feedparser
import requests

from config import REQUEST_HEADERS
from sources.base import BaseFetcher, Item

ARXIV_API = "https://export.arxiv.org/api/query"
ARXIV_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG"]

# arXiv 分类 → 友好标签
_CAT_LABELS = {
    "cs.AI": "AI", "cs.CL": "NLP", "cs.LG": "ML",
    "cs.CV": "CV", "cs.MA": "多智能体", "cs.RO": "机器人",
    "stat.ML": "ML",
}
_WS = re.compile(r"\s+")


def _clean(text: str) -> str:
    return _WS.sub(" ", text).strip()


class ArxivFetcher(BaseFetcher):
    source = "arxiv"
    source_label = "arXiv 论文"

    def fetch(self, limit: int = 5) -> list[Item]:
        # arXiv API 偶发 503/限流/超时：用 HTTPS + 礼貌 UA + 较长超时 + 重试兜底
        query = " OR ".join(f"cat:{c}" for c in ARXIV_CATEGORIES)
        params = {"search_query": query, "sortBy": "submittedDate",
                  "sortOrder": "descending", "max_results": max(limit * 4, 20)}
        headers = {**REQUEST_HEADERS,
                   "User-Agent": "ai-hotboard/1.0 (daily AI digest; +https://github.com)"}
        last_exc = None
        for _ in range(3):  # 最多重试 3 次
            try:
                resp = requests.get(ARXIV_API, params=params, headers=headers,
                                    timeout=25)
                resp.raise_for_status()
                return parse_arxiv(resp.content, limit, self.source, self.source_label)
            except Exception as e:  # noqa: BLE001
                last_exc = e
                time.sleep(3)  # arXiv 建议请求间隔 ≥3s
        raise last_exc


def parse_arxiv(content: bytes, limit: int = 5,
                source: str = "arxiv", source_label: str = "arXiv 论文") -> list[Item]:
    feed = feedparser.parse(content)
    items: list[Item] = []
    for e in feed.entries:
        title = _clean(e.get("title", ""))
        if not title:
            continue
        aid = (e.get("id", "") or "").strip()           # http://arxiv.org/abs/xxxx
        url = aid
        pdf = aid.replace("/abs/", "/pdf/") if "/abs/" in aid else ""
        abstract = _clean(e.get("summary", ""))[:280]

        cats = []
        seen = set()
        for t in (e.get("tags") or []):
            term = t.get("term", "") if isinstance(t, dict) else ""
            if term and term not in seen:
                seen.add(term)
                cats.append(term)
        chips = ["论文"] + [_CAT_LABELS.get(c, c) for c in cats[:2]]

        authors = []
        for a in (e.get("authors") or [])[:3]:
            name = a.get("name", "") if isinstance(a, dict) else str(a)
            if name:
                authors.append(name)
        published = (e.get("published", "") or "")[:10]   # YYYY-MM-DD

        meta_parts = [p for p in [
            "作者 · " + ", ".join(authors) if authors else "",
            f"📅 {published}" if published else "",
            "📄 PDF" if pdf else "",
        ] if p]

        items.append(Item(
            source=source, source_label=source_label, rank=0,
            title=title,
            url=url,
            score=0,
            score_label="",
            extra=cats[0] if cats else "",
            description=abstract,
            tags=chips,
            meta="  ·  ".join(meta_parts),
        ))
        if len(items) >= limit:
            break
    return items
