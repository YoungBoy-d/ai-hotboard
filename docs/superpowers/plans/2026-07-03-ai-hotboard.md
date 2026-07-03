# 科技 × AI 每日热点看板 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 每天自动聚合 6 个科技/AI 源的热点，经 Qwen 加工成中文日报，发布深色科技风交互 HTML 到 GitHub Pages，并向飞书推送互动卡片。

**Architecture:** Python 单进程编排：`sources/*` 各源抓取器（网络层 + 纯解析层分离，便于单测）→ `ai_summarizer` 调 DashScope 兼容端点 → `dashboard` Jinja2 渲染单文件 HTML → `feishu` 构造互动卡片。GitHub Actions 每天北京时间 09:30 跑：生成 → 部署 gh-pages → 发卡片。

**Tech Stack:** Python 3.11、requests、beautifulsoup4、feedparser、jinja2、openai SDK（DashScope 兼容模式）、pytest、GitHub Actions、GitHub Pages。

**Spec:** [docs/superpowers/specs/2026-07-03-ai-hotboard-design.md](../specs/2026-07-03-ai-hotboard-design.md)

---

## 文件结构

| 文件 | 职责 |
|---|---|
| `requirements.txt` | 依赖清单 |
| `.gitignore` | 忽略 output/、.env、缓存 |
| `.env.example` | 环境变量模板 |
| `conftest.py` | 把项目根加入 sys.path，供测试 import |
| `config.py` | 加载 .env，集中所有配置常量 |
| `sources/base.py` | `Item` 数据类 + `BaseFetcher`（含 `safe_fetch` 容错） |
| `sources/hackernews.py` 等 6 个 | 各源 `fetch()`（网络）+ `parse_x()`（纯函数，单测目标） |
| `ai_summarizer.py` | Qwen 调用 + JSON 解析 + 失败兜底 |
| `dashboard.py` | `build_report()` + `render_html()` |
| `templates/dashboard.html.j2` | 深色科技风单文件模板（内联 CSS/JS） |
| `feishu.py` | `build_card()` 构造卡片 + `send_card()` 发送（重试） |
| `send_card.py` | 读 output/payload.json → 发卡片（CI 末步） |
| `main.py` | 编排 + CLI（--source / --send） |
| `.github/workflows/daily.yml` | 定时 + 手动触发，生成→部署→发卡片 |
| `tests/test_*.py` | 各模块单测 |

**关键设计**：每个 fetcher 把"取字节流"和"解析成 Item 列表"拆开。网络层不可单测，解析层（纯函数）是 TDD 目标，用本地 fixture 喂数据。

**约定**：
- `Item.key` = `"{source}:{rank}"`，作为 AI translations 的映射键。
- `report` 字典（dashboard 与 feishu 共享）：`{date, weekday, editorial, sources:[{key,label,items:[{title,url,score_label,extra}]}], source_count, total}`。

---

## Task 1: 项目骨架与配置

**Files:**
- Create: `requirements.txt`, `.gitignore`, `.env.example`, `conftest.py`, `config.py`, `sources/__init__.py`

- [ ] **Step 1: 创建依赖与忽略文件**

`requirements.txt`:
```
requests>=2.31
beautifulsoup4>=4.12
feedparser>=6.0
jinja2>=3.1
openai>=1.10
python-dotenv>=1.0
pytest>=8.0
```

`.gitignore`:
```
output/
.env
__pycache__/
*.pyc
.pytest_cache/
```

`.env.example`:
```
# 通义千问 DashScope
DASHSCOPE_API_KEY=
# 飞书自定义机器人 webhook
FEISHU_WEBHOOK_URL=
# GitHub Pages 公网看板地址（卡片按钮指向，CI 用）
PAGES_BASE_URL=
# RSSHub 实例（可选，默认公共实例）
RSSHUB_BASE=https://rsshub.app
# Product Hunt 官方 token（可选）
PH_API_TOKEN=
```

- [ ] **Step 2: 创建 conftest.py 让测试能 import 项目模块**

`conftest.py`:
```python
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
```

`sources/__init__.py`:（空文件）

- [ ] **Step 3: 创建 config.py**

`config.py`:
```python
import os

from dotenv import load_dotenv

load_dotenv()

TOP_N = 5

# DashScope / 通义千问
DASHSCOPE_API_KEY = os.getenv("DASHSCOPE_API_KEY", "")
DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"
QWEN_MODEL = "qwen3.7-plus"

# 飞书
FEISHU_WEBHOOK_URL = os.getenv("FEISHU_WEBHOOK_URL", "")

# GitHub Pages 看板地址
PAGES_BASE_URL = os.getenv("PAGES_BASE_URL", "")

# RSSHub
RSSHUB_BASE = os.getenv("RSSHUB_BASE", "https://rsshub.app")

# Product Hunt 官方 token（可选）
PH_API_TOKEN = os.getenv("PH_API_TOKEN", "")

# HTTP 公共
REQUEST_TIMEOUT = 15
REQUEST_HEADERS = {"User-Agent": "Mozilla/5.0 (ai-hotboard daily digest)"}

# 源标识 → 展示名
SOURCES = {
    "hackernews": "Hacker News",
    "github": "GitHub Trending",
    "producthunt": "Product Hunt",
    "v2ex": "V2EX",
    "rss_zh": "36氪·少数派·虎嗅",
    "juejin": "掘金",
}
```

- [ ] **Step 4: 安装依赖并验证可 import**

Run: `pip install -r requirements.txt && python -c "import config; print(config.SOURCES)"`
Expected: 打印 6 个源的字典，无报错。

- [ ] **Step 5: Commit**

```bash
git add requirements.txt .gitignore .env.example conftest.py config.py sources/__init__.py
git commit -m "chore: project scaffold and config"
```

---

## Task 2: Item 数据模型与 BaseFetcher

**Files:**
- Create: `sources/base.py`
- Test: `tests/test_base.py`

- [ ] **Step 1: 写失败测试**

`tests/test_base.py`:
```python
from sources.base import Item, BaseFetcher


def test_item_key_and_display_title():
    it = Item(source="hackernews", source_label="Hacker News", rank=2,
              title="Hello AI", url="https://x.com")
    assert it.key == "hackernews:2"
    assert it.display_title == "Hello AI"  # title_zh 为空时回退原标题


def test_item_display_title_prefers_zh():
    it = Item(source="v2ex", source_label="V2EX", rank=1, title="abc",
              url="u", title_zh="中文化标题")
    assert it.display_title == "中文化标题"


def test_safe_fetch_assigns_rank_and_handles_error():
    class Boom(BaseFetcher):
        source = "x"
        source_label = "X"
        def fetch(self, limit=5):
            raise RuntimeError("boom")

    class Ok(BaseFetcher):
        source = "y"
        source_label = "Y"
        def fetch(self, limit=5):
            return [Item(source="y", source_label="Y", rank=0, title=f"t{i}", url="u")
                    for i in range(8)]

    assert Boom().safe_fetch(5) == []           # 异常 → 空列表，不抛
    ok = Ok().safe_fetch(5)
    assert [i.rank for i in ok] == [1, 2, 3, 4, 5]  # 截断 + 重排 rank
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_base.py -v`
Expected: FAIL（`ModuleNotFoundError: sources.base`）

- [ ] **Step 3: 实现 sources/base.py**

```python
from dataclasses import dataclass


@dataclass
class Item:
    source: str            # 源标识，如 "hackernews"
    source_label: str      # 展示名，如 "Hacker News"
    rank: int              # 源内排名 1..N（由 safe_fetch 赋值）
    title: str             # 原始标题
    url: str               # 原文链接
    score: int = 0         # 热度数值（用于排序/参考）
    score_label: str = ""  # 热度展示文案，如 "▲ 123"
    extra: str = ""        # 附加信息（语言/作者/子源等）
    title_zh: str = ""     # AI 中文化标题；为空时展示用 title

    @property
    def key(self) -> str:
        return f"{self.source}:{self.rank}"

    @property
    def display_title(self) -> str:
        return self.title_zh or self.title


class BaseFetcher:
    source: str = ""
    source_label: str = ""

    def fetch(self, limit: int = 5) -> list[Item]:
        raise NotImplementedError

    def safe_fetch(self, limit: int = 5) -> list[Item]:
        """容错抓取：异常返回空列表，截断到 limit 并重排 rank。"""
        try:
            items = self.fetch(limit) or []
        except Exception as e:  # noqa: BLE001
            print(f"[{self.source}] 获取失败: {e}")
            return []
        items = items[:limit]
        for i, it in enumerate(items):
            it.rank = i + 1
        return items
```

- [ ] **Step 4: 运行测试通过**

Run: `pytest tests/test_base.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: Commit**

```bash
git add sources/base.py tests/test_base.py
git commit -m "feat: Item dataclass and BaseFetcher with safe_fetch"
```

---

## Task 3: Hacker News 抓取器

**Files:**
- Create: `sources/hackernews.py`
- Test: `tests/test_hackernews.py`

- [ ] **Step 1: 写失败测试**

`tests/test_hackernews.py`:
```python
from sources.hackernews import parse_hn


def test_parse_hn_sorts_by_points_and_falls_back_url():
    data = {
        "hits": [
            {"objectID": "1", "title": "Low", "points": 10, "num_comments": 1,
             "url": "https://ext.com/1"},
            {"objectID": "2", "title": "High", "points": 500, "num_comments": 42,
             "url": None},  # Ask HN 无 url → 回退 HN 讨论页
            {"objectID": "3", "title": "Mid", "points": 100, "num_comments": 5,
             "url": "https://ext.com/3"},
        ]
    }
    items = parse_hn(data, limit=5)
    assert [i.title for i in items] == ["High", "Mid", "Low"]   # 按 points 降序
    assert items[0].score_label == "▲ 500"
    assert items[0].url == "https://news.ycombinator.com/item?id=2"  # 回退
    assert items[1].url == "https://ext.com/3"
    assert items[0].extra == "42 评论"
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_hackernews.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: 实现 sources/hackernews.py**

```python
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
```

- [ ] **Step 4: 运行测试通过**

Run: `pytest tests/test_hackernews.py -v`
Expected: PASS（1 passed）

- [ ] **Step 5: Commit**

```bash
git add sources/hackernews.py tests/test_hackernews.py
git commit -m "feat: Hacker News fetcher (Algolia API)"
```

---

## Task 4: V2EX 抓取器

**Files:**
- Create: `sources/v2ex.py`
- Test: `tests/test_v2ex.py`

- [ ] **Step 1: 写失败测试**

`tests/test_v2ex.py`:
```python
from sources.v2ex import parse_v2ex


def test_parse_v2ex_sorts_by_replies_and_uses_node():
    topics = [
        {"title": "A", "url": "https://www.v2ex.com/t/1", "replies": 3,
         "node": {"title": "Python"}},
        {"title": "B", "url": "https://www.v2ex.com/t/2", "replies": 30,
         "node": {"title": "程序员"}},
    ]
    items = parse_v2ex(topics, limit=5)
    assert [i.title for i in items] == ["B", "A"]
    assert items[0].score_label == "💬 30"
    assert items[0].extra == "程序员"
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_v2ex.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: 实现 sources/v2ex.py**

```python
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
```

- [ ] **Step 4: 运行测试通过**

Run: `pytest tests/test_v2ex.py -v`
Expected: PASS（1 passed）

- [ ] **Step 5: Commit**

```bash
git add sources/v2ex.py tests/test_v2ex.py
git commit -m "feat: V2EX fetcher (hot topics API)"
```

---

## Task 5: 掘金抓取器

**Files:**
- Create: `sources/juejin.py`
- Test: `tests/test_juejin.py`

- [ ] **Step 1: 写失败测试**

`tests/test_juejin.py`:
```python
from sources.juejin import parse_juejin


def test_parse_juejin_filters_pins_and_sorts_by_digg():
    data = {
        "data": [
            {"item_type": 2, "article_info": {"article_id": "a1", "title": "低赞"},
             "content_counter": {"dig_count": 5}},
            {"item_type": 4, "article_info": {"article_id": "p1", "title": "沸点"},
             "content_counter": {"dig_count": 999}},  # item_type!=2 → 沸点，过滤
            {"item_type": 2, "article_info": {"article_id": "a2", "title": "高赞"},
             "content_counter": {"dig_count": 200}},
        ]
    }
    items = parse_juejin(data, limit=5)
    assert [i.title for i in items] == ["高赞", "低赞"]
    assert items[0].url == "https://juejin.cn/post/a2"
    assert items[0].score_label == "👍 200"
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_juejin.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: 实现 sources/juejin.py**

```python
import requests

from config import REQUEST_HEADERS, REQUEST_TIMEOUT
from sources.base import BaseFetcher, Item

JUEJIN_API = "https://api.juejin.cn/recommend_api/v1/article/recommend_all_feed"


class JuejinFetcher(BaseFetcher):
    source = "juejin"
    source_label = "掘金"

    def fetch(self, limit: int = 5) -> list[Item]:
        resp = requests.post(
            JUEJIN_API,
            json={"id_type": 2, "sort_type": 200, "cursor": "0", "limit": 20},
            headers=REQUEST_HEADERS,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return parse_juejin(resp.json(), limit, self.source, self.source_label)


def parse_juejin(data: dict, limit: int = 5,
                 source: str = "juejin", source_label: str = "掘金") -> list[Item]:
    rows = data.get("data", []) or []
    rows = [r for r in rows if r.get("item_type", 2) == 2]  # 仅文章，过滤沸点
    rows = sorted(
        rows,
        key=lambda r: (r.get("content_counter") or {}).get("dig_count", 0) or 0,
        reverse=True,
    )
    items: list[Item] = []
    for r in rows[:limit]:
        info = r.get("article_info") or {}
        aid = info.get("article_id", "")
        dig = (r.get("content_counter") or {}).get("dig_count", 0) or 0
        items.append(Item(
            source=source, source_label=source_label, rank=0,
            title=info.get("title", "") or "",
            url=f"https://juejin.cn/post/{aid}",
            score=dig,
            score_label=f"👍 {dig}",
            extra="",
        ))
    return items
```

- [ ] **Step 4: 运行测试通过**

Run: `pytest tests/test_juejin.py -v`
Expected: PASS（1 passed）

- [ ] **Step 5: Commit**

```bash
git add sources/juejin.py tests/test_juejin.py
git commit -m "feat: Juejin fetcher (recommend feed API)"
```

---

## Task 6: GitHub Trending 抓取器

**Files:**
- Create: `sources/github_trending.py`
- Test: `tests/test_github_trending.py`

- [ ] **Step 1: 写失败测试**

`tests/test_github_trending.py`:
```python
from sources.github_trending import parse_trending

FIXTURE = """
<section><article class="Box-row">
  <h2><a href="/owner/repo-a">repo-a</a></h2>
  <span itemprop="programmingLanguage">Python</span>
  <a class="Link Link--muted" href="/owner/repo-a/stargazers">100</a>
  <span class="d-inline-block float-sm-right">12 stars today</span>
</article>
<article class="Box-row">
  <h2><a href="/owner/repo-b">repo-b</a></h2>
  <a class="Link Link--muted" href="/owner/repo-b/stargazers">50</a>
</article></section>
"""


def test_parse_trending_extracts_repo_lang_and_stars():
    items = parse_trending(FIXTURE, limit=5)
    assert [i.title for i in items] == ["owner/repo-a", "owner/repo-b"]
    assert items[0].url == "https://github.com/owner/repo-a"
    assert items[0].extra == "Python"
    assert "12 stars today" in items[0].score_label
    # 缺语言/今日星数也不应报错
    assert items[1].extra == ""
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_github_trending.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: 实现 sources/github_trending.py**

```python
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
```

- [ ] **Step 4: 运行测试通过**

Run: `pytest tests/test_github_trending.py -v`
Expected: PASS（1 passed）

- [ ] **Step 5: Commit**

```bash
git add sources/github_trending.py tests/test_github_trending.py
git commit -m "feat: GitHub Trending fetcher (HTML scrape)"
```

---

## Task 7: Product Hunt 抓取器（RSSHub）

**Files:**
- Create: `sources/producthunt.py`
- Test: `tests/test_producthunt.py`

- [ ] **Step 1: 写失败测试**

`tests/test_producthunt.py`:
```python
from sources.producthunt import parse_ph


def test_parse_ph_extracts_title_link_author():
    entries = [
        {"title": "Cool App", "link": "https://producthunt.com/posts/cool",
         "author": "alice"},
        {"title": "Next Big Thing", "link": "https://producthunt.com/posts/next",
         "author": "bob"},
    ]
    items = parse_ph(entries, limit=5)
    assert [i.title for i in items] == ["Cool App", "Next Big Thing"]
    assert items[0].url == "https://producthunt.com/posts/cool"
    assert items[0].extra == "alice"


def test_parse_ph_handles_missing_fields():
    items = parse_ph([{}], limit=5)
    assert len(items) == 1
    assert items[0].title == ""
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_producthunt.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: 实现 sources/producthunt.py**

```python
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
```

- [ ] **Step 4: 运行测试通过**

Run: `pytest tests/test_producthunt.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add sources/producthunt.py tests/test_producthunt.py
git commit -m "feat: Product Hunt fetcher (RSSHub)"
```

---

## Task 8: 中文科技 RSS 抓取器

**Files:**
- Create: `sources/rss_zh.py`
- Test: `tests/test_rss_zh.py`

- [ ] **Step 1: 写失败测试**

`tests/test_rss_zh.py`:
```python
import time

from sources.rss_zh import parse_rss_entry


def _entry(title, day, sub):
    return {
        "title": title,
        "link": f"https://x.com/{title}",
        "published_parsed": time.strptime(f"2026-07-{day:02d}", "%Y-%m-%d"),
        "author": sub,
    }


def test_parse_rss_entry_stamps_subsource_in_extra():
    e = _entry("AI 改变世界", 3, "少数派")
    it = parse_rss_entry(e, source="rss_zh", source_label="36氪·少数派·虎嗅",
                         sub_label="少数派")
    assert it.title == "AI 改变世界"
    assert it.url == "https://x.com/AI 改变世界"
    assert it.extra == "少数派"
    assert it.score == int(time.mktime(time.strptime("2026-07-03", "%Y-%m-%d")))


def test_parse_rss_entry_without_published():
    it = parse_rss_entry({"title": "x", "link": "u"}, source="rss_zh",
                         source_label="L", sub_label="36氪")
    assert it.score == 0  # 缺时间 → 0，排序沉底
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_rss_zh.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: 实现 sources/rss_zh.py**

```python
import time

import feedparser

from config import REQUEST_HEADERS, RSSHUB_BASE
from sources.base import BaseFetcher, Item

SSPAI_FEED = "https://sspai.com/feed"


class RssZhFetcher(BaseFetcher):
    source = "rss_zh"
    source_label = "36氪·少数派·虎嗅"

    def _feeds(self) -> list[tuple[str, str]]:
        return [
            ("少数派", SSPAI_FEED),
            ("36氪", f"{RSSHUB_BASE}/36kr/newsflashes"),
            ("虎嗅", f"{RSSHUB_BASE}/huxiu/article"),
        ]

    def fetch(self, limit: int = 5) -> list[Item]:
        all_items: list[Item] = []
        for sub_label, url in self._feeds():
            d = feedparser.parse(url, request_headers=REQUEST_HEADERS)
            for e in d.entries:
                all_items.append(parse_rss_entry(
                    e, self.source, self.source_label, sub_label))
        # 按发布时间倒序，取最新 limit
        all_items.sort(key=lambda it: it.score, reverse=True)
        return all_items[:limit]


def parse_rss_entry(entry, source: str, source_label: str, sub_label: str) -> Item:
    published = entry.get("published_parsed")
    ts = int(time.mktime(published)) if published else 0
    return Item(
        source=source, source_label=source_label, rank=0,
        title=entry.get("title", "") or "",
        url=entry.get("link", "") or "",
        score=ts,
        score_label="",
        extra=sub_label,
    )
```

- [ ] **Step 4: 运行测试通过**

Run: `pytest tests/test_rss_zh.py -v`
Expected: PASS（2 passed）

- [ ] **Step 5: Commit**

```bash
git add sources/rss_zh.py tests/test_rss_zh.py
git commit -m "feat: Chinese tech RSS fetcher (sspai + RSSHub 36kr/huxiu)"
```

---

## Task 9: AI 摘要（ai_summarizer.py）

**Files:**
- Create: `ai_summarizer.py`
- Test: `tests/test_ai_summarizer.py`

- [ ] **Step 1: 写失败测试**

`tests/test_ai_summarizer.py`:
```python
import json

from ai_summarizer import summarize, build_prompt
from sources.base import Item


def _item(source, rank, title):
    return Item(source=source, source_label=source, rank=rank, title=title, url="u")


class _Msg:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Msg(content)


class _Resp:
    def __init__(self, content):
        self.choices = [_Choice(content)]


class _Completions:
    def __init__(self, content, exc):
        self._content = content
        self._exc = exc

    def create(self, **kwargs):
        if self._exc:
            raise self._exc
        return _Resp(self._content)


class _Chat:
    def __init__(self, completions):
        self.completions = completions


class FakeClient:
    """模拟 openai.OpenAI 的 chat.completions.create 调用链。"""
    def __init__(self, content, exc=None):
        self.chat = _Chat(_Completions(content, exc))


def test_build_prompt_includes_each_item_key():
    items = [_item("hackernews", 1, "GPT-5 released")]
    prompt = build_prompt(items)
    assert "[hackernews:1]" in prompt
    assert "GPT-5 released" in prompt


def test_summarize_parses_json():
    payload = {"editorial": [{"text": "AI 大爆发", "refs": ["hackernews:1"]}],
               "translations": {"hackernews:1": "GPT-5 发布"}}
    client = FakeClient(json.dumps(payload))
    result = summarize([_item("hackernews", 1, "GPT-5 released")], client=client)
    assert result["editorial"][0]["text"] == "AI 大爆发"
    assert result["translations"]["hackernews:1"] == "GPT-5 发布"


def test_summarize_falls_back_on_exception():
    client = FakeClient("", exc=RuntimeError("api down"))
    result = summarize([_item("hackernews", 1, "x")], client=client)
    assert result == {"editorial": [], "translations": {}}
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_ai_summarizer.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: 实现 ai_summarizer.py**

```python
import json

from openai import OpenAI

from config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, QWEN_MODEL


def build_prompt(items) -> str:
    catalog = "\n".join(f"[{it.key}] ({it.source_label}) {it.title}" for it in items)
    return f"""下面是今日各科技/AI 热点榜的条目（[key] 为编号）：

{catalog}

请完成两件事，严格以 JSON 返回：
1. editorial：3-5 条"今日要点"，每条形如 {{"text":"一句话中文摘要","refs":["key1",...]}}，refs 引用上面的编号。
2. translations：仅对【英文】条目给出简短中文标题，形如 {{"key":"中文标题"}}；中文条目不要包含。

只输出 JSON，不要任何解释或多余文字。格式：
{{"editorial":[...],"translations":{{...}}}}"""


def summarize(items, client=None) -> dict:
    """返回 {"editorial": [...], "translations": {...}}；任何失败都兜底为空。"""
    if client is None:
        if not DASHSCOPE_API_KEY:
            print("[ai] 未配置 DASHSCOPE_API_KEY，跳过摘要")
            return {"editorial": [], "translations": {}}
        client = OpenAI(api_key=DASHSCOPE_API_KEY, base_url=DASHSCOPE_BASE_URL)

    try:
        resp = client.chat.completions.create(
            model=QWEN_MODEL,
            messages=[{"role": "user", "content": build_prompt(items)}],
            response_format={"type": "json_object"},
            temperature=0.5,
        )
        content = resp.choices[0].message.content
        data = json.loads(content)
        return {
            "editorial": data.get("editorial", []) or [],
            "translations": data.get("translations", {}) or {},
        }
    except Exception as e:  # noqa: BLE001
        print(f"[ai] 摘要失败，使用兜底: {e}")
        return {"editorial": [], "translations": {}}
```

- [ ] **Step 4: 运行测试通过**

Run: `pytest tests/test_ai_summarizer.py -v`
Expected: PASS（3 passed）

- [ ] **Step 5: Commit**

```bash
git add ai_summarizer.py tests/test_ai_summarizer.py
git commit -m "feat: AI summarizer via Qwen (DashScope compatible mode)"
```

---

## Task 10: HTML 看板渲染（dashboard.py + 模板）

**Files:**
- Create: `dashboard.py`, `templates/dashboard.html.j2`
- Test: `tests/test_dashboard.py`

- [ ] **Step 1: 写失败测试**

`tests/test_dashboard.py`:
```python
import datetime

from sources.base import Item
from dashboard import build_report, render_html


def _item(source, rank, title, extra=""):
    return Item(source=source, source_label=source, rank=rank,
                title=title, url="https://x.com", score_label="▲ 10", extra=extra)


def test_build_report_shape():
    items_by_source = [
        ("hackernews", "Hacker News", [_item("hackernews", 1, "AI Boom")]),
    ]
    ai = {"editorial": [{"text": "要点一", "refs": []}], "translations": {}}
    report = build_report(items_by_source, ai, today=datetime.date(2026, 7, 3))
    assert report["date"] == "2026-07-03"
    assert report["weekday"] == "周五"
    assert report["source_count"] == 1
    assert report["total"] == 1
    assert report["sources"][0]["items"][0]["title"] == "AI Boom"


def test_render_html_contains_key_sections():
    items_by_source = [
        ("hackernews", "Hacker News", [_item("hackernews", 1, "AI Boom")]),
    ]
    ai = {"editorial": [{"text": "今日要点一", "refs": []}], "translations": {}}
    report = build_report(items_by_source, ai, today=datetime.date(2026, 7, 3))
    html = render_html(report)
    assert "科技" in html and "AI" in html              # 标题
    assert "今日要点一" in html                          # AI 导语
    assert "Hacker News" in html                        # 源标签
    assert "AI Boom" in html                            # 条目标题
    assert "2026-07-03" in html                         # 日期
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_dashboard.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: 实现 dashboard.py**

```python
import datetime
import os

from jinja2 import Environment, FileSystemLoader, select_autoescape

from sources.base import Item

TMPL_DIR = os.path.join(os.path.dirname(__file__), "templates")
_env = Environment(
    loader=FileSystemLoader(TMPL_DIR),
    autoescape=select_autoescape(["html", "xml"]),
)
_WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _item_view(it: Item) -> dict:
    return {
        "title": it.display_title,
        "url": it.url,
        "score_label": it.score_label,
        "extra": it.extra,
        "source": it.source,
        "source_label": it.source_label,
    }


def build_report(items_by_source, ai_result: dict,
                 today: datetime.date | None = None) -> dict:
    today = today or datetime.date.today()
    sources = []
    for src_key, label, src_items in items_by_source:
        sources.append({
            "key": src_key,
            "label": label,
            "items": [_item_view(it) for it in src_items],
        })
    return {
        "date": today.strftime("%Y-%m-%d"),
        "weekday": _WEEKDAYS[today.weekday()],
        "editorial": ai_result.get("editorial", []) or [],
        "sources": sources,
        "source_count": len(sources),
        "total": sum(len(s["items"]) for s in sources),
    }


def render_html(report: dict) -> str:
    tmpl = _env.get_template("dashboard.html.j2")
    return tmpl.render(report=report)
```

- [ ] **Step 4: 实现模板 templates/dashboard.html.j2**

```jinja
<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>科技 × AI 每日热点 · {{ report.date }}</title>
<style>
  :root{
    --bg:#0B0F1A; --bg-card:rgba(255,255,255,.04); --border:rgba(255,255,255,.08);
    --text:#E6EAF2; --muted:#8A93A6; --accent:#22D3EE; --accent2:#A78BFA;
    --grad:linear-gradient(135deg,#22D3EE 0%,#A78BFA 100%);
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);background-image:radial-gradient(900px 500px at 80% -10%,rgba(167,139,250,.15),transparent),radial-gradient(700px 400px at 0% 0%,rgba(34,211,238,.12),transparent);color:var(--text);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","PingFang SC","Microsoft YaHei",sans-serif;line-height:1.6;padding:24px}
  .wrap{max-width:1080px;margin:0 auto}
  header{display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:12px;margin-bottom:22px}
  .brand{display:flex;align-items:center;gap:14px}
  .logo{width:46px;height:46px;border-radius:13px;background:var(--grad);display:flex;align-items:center;justify-content:center;font-size:24px;box-shadow:0 8px 24px rgba(34,211,238,.3)}
  h1{font-size:24px;font-weight:700}
  .sub{color:var(--muted);font-size:13px}
  .date-pill{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;background:var(--bg-card);border:1px solid var(--border);padding:8px 14px;border-radius:999px;font-size:13px;color:var(--muted)}
  .editorial{background:var(--bg-card);border:1px solid var(--border);backdrop-filter:blur(10px);border-radius:18px;padding:20px 22px;margin-bottom:22px}
  .editorial h2{font-size:15px;color:var(--accent);margin-bottom:12px;letter-spacing:.5px}
  .editorial ul{list-style:none;display:flex;flex-direction:column;gap:10px}
  .editorial li{font-size:15px;padding-left:18px;position:relative}
  .editorial li::before{content:"▸";position:absolute;left:0;color:var(--accent2)}
  .grid{display:grid;grid-template-columns:repeat(2,1fr);gap:18px}
  .card{background:var(--bg-card);border:1px solid var(--border);backdrop-filter:blur(10px);border-radius:18px;padding:18px 20px;transition:transform .15s,border-color .15s}
  .card:hover{transform:translateY(-2px);border-color:rgba(34,211,238,.35)}
  .card h3{font-size:16px;margin-bottom:14px;display:flex;align-items:center;gap:8px}
  .card ol{list-style:none;counter-reset:rank;display:flex;flex-direction:column;gap:9px}
  .card li{counter-increment:rank;display:flex;gap:10px;align-items:baseline;font-size:14px}
  .card li::before{content:counter(rank);flex:0 0 auto;width:20px;height:20px;border-radius:6px;background:rgba(255,255,255,.06);color:var(--muted);font-size:11px;display:flex;align-items:center;justify-content:center;font-family:ui-monospace,monospace}
  .card a{color:var(--text);text-decoration:none;border-bottom:1px solid transparent;transition:border-color .15s,color .15s}
  .card a:hover{color:var(--accent);border-bottom-color:var(--accent)}
  .score{color:var(--accent);font-size:12px;font-family:ui-monospace,monospace;white-space:nowrap}
  .extra{color:var(--muted);font-size:12px}
  .empty{color:var(--muted);font-style:italic;font-size:13px}
  footer{text-align:center;color:var(--muted);font-size:12px;margin-top:26px;font-family:ui-monospace,monospace}
  @media (max-width:720px){.grid{grid-template-columns:1fr}}
</style>
</head>
<body>
<div class="wrap">
  <header>
    <div class="brand">
      <div class="logo">🤖</div>
      <div>
        <h1>科技 × AI 每日热点</h1>
        <div class="sub">Daily Tech &amp; AI Digest</div>
      </div>
    </div>
    <div class="date-pill">{{ report.date }} {{ report.weekday }}</div>
  </header>

  {% if report.editorial %}
  <section class="editorial">
    <h2>📌 今日要点 · AI 编辑</h2>
    <ul>
      {% for e in report.editorial %}
      <li>{{ e.text }}</li>
      {% endfor %}
    </ul>
  </section>
  {% endif %}

  <div class="grid">
    {% for s in report.sources %}
    <section class="card">
      <h3>{{ s.label }}</h3>
      {% if s.items %}
      <ol>
        {% for it in s.items %}
        <li>
          <a href="{{ it.url }}" target="_blank" rel="noopener">{{ it.title }}</a>
          {% if it.score_label %}<span class="score">{{ it.score_label }}</span>{% endif %}
          {% if it.extra %}<span class="extra">· {{ it.extra }}</span>{% endif %}
        </li>
        {% endfor %}
      </ol>
      {% else %}
      <div class="empty">该源获取失败，稍后重试</div>
      {% endif %}
    </section>
    {% endfor %}
  </div>

  <footer>数据源 {{ report.source_count }} · 共 {{ report.total }} 条 · 生成于 {{ report.date }} · by Claude</footer>
</div>
</body>
</html>
```

- [ ] **Step 5: 运行测试通过**

Run: `pytest tests/test_dashboard.py -v`
Expected: PASS（2 passed）

- [ ] **Step 6: Commit**

```bash
git add dashboard.py templates/dashboard.html.j2 tests/test_dashboard.py
git commit -m "feat: dark-tech interactive HTML dashboard renderer"
```

---

## Task 11: 飞书互动卡片（feishu.py）

**Files:**
- Create: `feishu.py`
- Test: `tests/test_feishu.py`

- [ ] **Step 1: 写失败测试**

`tests/test_feishu.py`:
```python
from unittest.mock import patch, MagicMock

from feishu import build_card, send_card


def _report():
    return {
        "date": "2026-07-03", "weekday": "周五",
        "source_count": 1, "total": 1,
        "editorial": [{"text": "AI 大事件", "refs": []}],
        "sources": [{"key": "hackernews", "label": "Hacker News",
                     "items": [{"title": "GPT-5", "url": "https://x.com",
                                "score_label": "▲ 10", "extra": ""}]}],
    }


def test_build_card_structure_and_link_button():
    card = build_card(_report(), base_url="https://u.github.io/p/")
    assert card["msg_type"] == "interactive"
    assert "2026-07-03" in card["card"]["header"]["title"]["content"]
    elements = card["card"]["elements"]
    # 含 AI 要点、源 section、跳转按钮
    joined = str(elements)
    assert "AI 大事件" in joined
    assert "Hacker News" in joined
    assert "GPT-5" in joined
    action = [e for e in elements if e.get("tag") == "action"][0]
    assert action["actions"][0]["url"] == "https://u.github.io/p/"


def test_build_card_empty_source_shows_failed():
    report = _report()
    report["sources"][0]["items"] = []
    card = build_card(report, base_url="")
    assert "获取失败" in str(card["card"]["elements"])


def test_send_card_success():
    fake = MagicMock()
    fake.json.return_value = {"code": 0, "msg": "success"}
    with patch("feishu.requests.post", return_value=fake) as p:
        ok = send_card({"msg_type": "interactive", "card": {}},
                       webhook="https://hook")
    assert ok is True
    p.assert_called_once()


def test_send_card_retries_then_gives_up():
    fake = MagicMock()
    fake.json.return_value = {"code": 19021, "msg": "bad"}
    with patch("feishu.requests.post", return_value=fake) as p, \
         patch("feishu.time.sleep"):
        ok = send_card({"msg_type": "interactive", "card": {}},
                       webhook="https://hook", retries=1)
    assert ok is False
    assert p.call_count == 2  # 1 次 + 1 次重试
```

- [ ] **Step 2: 运行确认失败**

Run: `pytest tests/test_feishu.py -v`
Expected: FAIL（`ModuleNotFoundError`）

- [ ] **Step 3: 实现 feishu.py**

```python
import time

import requests

from config import FEISHU_WEBHOOK_URL


def build_card(report: dict, base_url: str = "") -> dict:
    elements: list[dict] = []

    ed = report.get("editorial", []) or []
    if ed:
        lines = ["📌 **今日要点 · AI 编辑**"]
        for e in ed:
            lines.append(f"• {e.get('text', '')}")
        elements.append({"tag": "div",
                         "text": {"tag": "lark_md", "content": "\n".join(lines)}})
        elements.append({"tag": "hr"})

    for s in report.get("sources", []):
        items = s.get("items", [])
        if not items:
            content = f"**{s['label']}**\n_获取失败，稍后重试_"
        else:
            lines = [f"**{s['label']}**"]
            for i, it in enumerate(items):
                extra = f" · {it['extra']}" if it.get("extra") else ""
                score = f" {it['score_label']}" if it.get("score_label") else ""
                lines.append(f"{i + 1}. [{it['title']}]({it['url']}){score}{extra}")
            content = "\n".join(lines)
        elements.append({"tag": "div", "text": {"tag": "lark_md", "content": content}})
        elements.append({"tag": "hr"})

    if base_url:
        elements.append({"tag": "action", "actions": [
            {"tag": "button", "text": {"tag": "plain_text", "content": "🌐 查看完整看板"},
             "url": base_url, "type": "primary"}
        ]})

    note = (f"数据源 {report.get('source_count', 0)} · 共 {report.get('total', 0)} 条"
            f" · 生成于 {report.get('date', '')}")
    elements.append({"tag": "note",
                     "elements": [{"tag": "plain_text", "content": note}]})

    title = f"🤖 科技×AI 每日热点 · {report.get('date', '')} {report.get('weekday', '')}"
    return {
        "msg_type": "interactive",
        "card": {
            "config": {"wide_screen": True},
            "header": {"title": {"tag": "plain_text", "content": title},
                       "template": "blue"},
            "elements": elements,
        },
    }


def send_card(card: dict, webhook: str = "", retries: int = 1) -> bool:
    webhook = webhook or FEISHU_WEBHOOK_URL
    last = None
    for _ in range(retries + 1):
        try:
            resp = requests.post(webhook, json=card, timeout=15)
            data = resp.json()
            # 飞书成功：{"code":0,...} 或 {"StatusCode":0,...}
            if data.get("code", -1) == 0 or data.get("StatusCode", -1) == 0:
                return True
            last = data
        except Exception as e:  # noqa: BLE001
            last = str(e)
        time.sleep(1)
    print(f"[feishu] 发送失败: {last}")
    return False
```

- [ ] **Step 4: 运行测试通过**

Run: `pytest tests/test_feishu.py -v`
Expected: PASS（4 passed）

- [ ] **Step 5: Commit**

```bash
git add feishu.py tests/test_feishu.py
git commit -m "feat: Feishu interactive card builder and sender"
```

---

## Task 12: send_card.py 入口（CI 末步）

**Files:**
- Create: `send_card.py`

- [ ] **Step 1: 实现 send_card.py**

```python
import json
import os

from config import PAGES_BASE_URL
from feishu import build_card, send_card


def main() -> int:
    payload_path = os.path.join(os.path.dirname(__file__), "output", "payload.json")
    with open(payload_path, encoding="utf-8") as f:
        report = json.load(f)
    card = build_card(report, PAGES_BASE_URL)
    ok = send_card(card)
    print("飞书卡片发送" + ("成功" if ok else "失败"))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: Commit**

```bash
git add send_card.py
git commit -m "feat: send_card entry point reading payload.json"
```

---

## Task 13: 主编排（main.py）

**Files:**
- Create: `main.py`

- [ ] **Step 1: 实现 main.py**

```python
import argparse
import json
import os
from concurrent.futures import ThreadPoolExecutor

from ai_summarizer import summarize
from config import SOURCES, TOP_N, PAGES_BASE_URL
from dashboard import build_report, render_html
from feishu import build_card, send_card
from sources.github_trending import GitHubTrendingFetcher
from sources.hackernews import HackerNewsFetcher
from sources.juejin import JuejinFetcher
from sources.producthunt import ProductHuntFetcher
from sources.rss_zh import RssZhFetcher
from sources.v2ex import V2EXFetcher

FETCHERS = {
    "hackernews": HackerNewsFetcher,
    "github": GitHubTrendingFetcher,
    "producthunt": ProductHuntFetcher,
    "v2ex": V2EXFetcher,
    "rss_zh": RssZhFetcher,
    "juejin": JuejinFetcher,
}
OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
ORDER = list(FETCHERS.keys())  # 卡片/看板的源展示顺序


def fetch_all(only: str | None = None) -> dict:
    keys = [only] if only else ORDER

    def _do(key):
        return key, FETCHERS[key]().safe_fetch(TOP_N)

    with ThreadPoolExecutor(max_workers=len(keys)) as ex:
        return dict(ex.map(_do, keys))


def main() -> int:
    parser = argparse.ArgumentParser(description="科技×AI 每日热点看板")
    parser.add_argument("--source", default=None, choices=ORDER,
                        help="仅抓取单个源（调试）")
    parser.add_argument("--send", action="store_true",
                        help="立即发送飞书卡片（本地真发测试）")
    args = parser.parse_args()

    results = fetch_all(args.source)

    order = [args.source] if args.source else ORDER
    items_by_source = [(k, SOURCES.get(k, k), results.get(k, [])) for k in order]

    all_items = [it for _, _, its in items_by_source for it in its]
    ai = summarize(all_items)
    for it in all_items:
        zh = ai["translations"].get(it.key)
        if zh:
            it.title_zh = zh

    report = build_report(items_by_source, ai)

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(os.path.join(OUTPUT_DIR, "index.html"), "w", encoding="utf-8") as f:
        f.write(render_html(report))
    with open(os.path.join(OUTPUT_DIR, "payload.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"已生成 output/index.html（{report['total']} 条，源 {report['source_count']}）")

    if args.send:
        card = build_card(report, PAGES_BASE_URL)
        ok = send_card(card)
        print("飞书卡片发送" + ("成功" if ok else "失败"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 2: 本地联调（需 .env 配好 key 与 webhook）**

Run: `python main.py`
Expected: 打印 `已生成 output/index.html（...）`；浏览器打开 `output/index.html` 看视觉。无 DASHSCOPE_API_KEY 时 AI 部分兜底为空也不报错。

- [ ] **Step 3: 单源调试**

Run: `python main.py --source hackernews`
Expected: index.html 只含 Hacker News 一个源。

- [ ] **Step 4: 真发飞书**

Run: `python main.py --send`
Expected: 飞书群收到互动卡片；终端打印"发送成功"。

- [ ] **Step 5: 跑全量单测确保无回归**

Run: `pytest -v`
Expected: 全部 PASS。

- [ ] **Step 6: Commit**

```bash
git add main.py
git commit -m "feat: main orchestrator with CLI (source/send)"
```

---

## Task 14: GitHub Actions 工作流

**Files:**
- Create: `.github/workflows/daily.yml`

- [ ] **Step 1: 实现工作流**

`.github/workflows/daily.yml`:
```yaml
name: Daily AI Hot Board

on:
  schedule:
    - cron: "30 1 * * *"   # UTC 01:30 = 北京时间 09:30
  workflow_dispatch:         # 支持手动触发

# gh-pages 部署权限
permissions:
  contents: write

jobs:
  build:
    runs-on: ubuntu-latest
    env:
      DASHSCOPE_API_KEY: ${{ secrets.DASHSCOPE_API_KEY }}
      FEISHU_WEBHOOK_URL: ${{ secrets.FEISHU_WEBHOOK_URL }}
      PAGES_BASE_URL: ${{ vars.PAGES_BASE_URL }}
      RSSHUB_BASE: ${{ vars.RSSHUB_BASE }}
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install deps
        run: pip install -r requirements.txt

      - name: Generate dashboard
        run: python main.py

      - name: Deploy to GitHub Pages
        uses: peaceiris/actions-gh-pages@v4
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./output

      - name: Send Feishu card
        run: python send_card.py
```

- [ ] **Step 2: Commit**

```bash
git add .github/workflows/daily.yml
git commit -m "ci: daily workflow (cron BJ 09:30, deploy gh-pages, send card)"
```

- [ ] **Step 3: 推送后配置 GitHub 仓库（人工，一次性）**

1. `git push -u origin main` 推到 GitHub。
2. **Settings → Secrets and variables → Actions**：
   - Secrets 新增：`DASHSCOPE_API_KEY`、`FEISHU_WEBHOOK_URL`
   - Variables 新增：`PAGES_BASE_URL`（值为 `https://<用户名>.github.io/<仓库名>/`）、可选 `RSSHUB_BASE`
3. **Settings → Pages**：Source 选 `Deploy from a branch`，分支 `gh-pages` / `/ (root)`，保存。
4. **Actions** 页手动 `workflow_dispatch` 触发一次，确认：gh-pages 被创建、Pages 可访问、飞书收到卡片。

- [ ] **Step 4: 验证端到端**

Expected: 工作流绿 ✓；`PAGES_BASE_URL` 打开是当日深色看板；飞书群收到含"查看完整看板"按钮的卡片。

---

## 完成标准

- [ ] 全量 `pytest` 通过。
- [ ] 本地 `python main.py` 生成 index.html，视觉符合深色科技风。
- [ ] 本地 `python main.py --send` 飞书收到卡片。
- [ ] CI `workflow_dispatch` 端到端跑通：gh-pages 更新 + 飞书卡片。
- [ ] 次日 09:30 自动触发（抽查一次）。
