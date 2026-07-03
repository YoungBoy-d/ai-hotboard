import requests
from bs4 import BeautifulSoup

from config import REQUEST_HEADERS, REQUEST_TIMEOUT
from sources.base import BaseFetcher, Item

GITHUB_TRENDING = "https://github.com/trending"


class GitHubTrendingFetcher(BaseFetcher):
    source = "github"
    source_label = "GitHub Trending"

    def fetch(self, limit: int = 5) -> list[Item]:
        resp = requests.get(
            GITHUB_TRENDING,
            params={"since": "daily"},
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return parse_trending(resp.text, limit, self.source, self.source_label)


def parse_trending(html: str, limit: int = 5,
                   source: str = "github",
                   source_label: str = "GitHub Trending") -> list[Item]:
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

        today = ""
        span = row.select_one("span.d-inline-block.float-sm-right")
        if span:
            today = span.get_text(strip=True)

        items.append(Item(
            source=source, source_label=source_label, rank=0,
            title=repo, url=url, score=0,
            score_label=("⭐ " + today) if today else "",
            extra=lang,
        ))
    return items
