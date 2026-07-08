import requests
from bs4 import BeautifulSoup

from config import REQUEST_HEADERS, REQUEST_TIMEOUT, is_ai_related
from sources.base import BaseFetcher, Item

GITHUB_TRENDING = "https://github.com/trending"

_TODAY = ("today", "this week", "this month")  # 趋势跨度文案识别


class GitHubTrendingFetcher(BaseFetcher):
    source = "github"
    source_label = "GitHub AI 仓库"

    def fetch(self, limit: int = 5) -> list[Item]:
        resp = requests.get(
            GITHUB_TRENDING,
            params={"since": "daily"},
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        # 先解析整个趋势榜，再按 AI 关键词过滤，保证 limit 条都是 AI 相关
        pool = parse_trending(resp.text, limit=999, source=self.source,
                              source_label=self.source_label)
        ai = [it for it in pool if is_ai_related(f"{it.title} {it.description}")]
        return ai[:limit]


def parse_trending(html: str, limit: int = 5,
                   source: str = "github",
                   source_label: str = "GitHub AI 仓库") -> list[Item]:
    soup = BeautifulSoup(html, "html.parser")
    items: list[Item] = []
    for row in soup.select("article.Box-row")[:limit]:
        a = row.select_one("h2 a")
        if not a:
            continue
        href = (a.get("href") or "").strip()
        repo = href.strip("/")
        url = "https://github.com" + href

        lang_el = row.select_one("[itemprop='programmingLanguage']")
        lang = lang_el.get_text(strip=True) if lang_el else ""

        # 今日/本周 star 增长
        today = ""
        span = row.select_one("span.d-inline-block.float-sm-right")
        if span:
            today = span.get_text(strip=True)

        # 总 star 数（stargazers 链接文本，如 "1.2k"）
        total = ""
        star_a = row.select_one("a[href$='/stargazers']")
        if star_a:
            total = star_a.get_text(strip=True)

        # 仓库简介（行内唯一 <p>）
        desc_el = row.select_one("p")
        desc = desc_el.get_text(strip=True) if desc_el else ""

        score_parts = []
        if today:
            score_parts.append(f"★ {today}")
        if total:
            score_parts.append(f"★ {total} 总")
        score_label = " · ".join(score_parts)

        chips = ["开源"]
        if lang:
            chips.append(lang)

        items.append(Item(
            source=source, source_label=source_label, rank=0,
            title=repo, url=url, score=0,
            score_label=score_label,
            extra="",
            description=desc,
            tags=chips,
            meta=f"语言 · {lang}" if lang else "",
        ))
    return items
