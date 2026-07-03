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
