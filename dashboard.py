import datetime
import os
from urllib.parse import urlparse

from jinja2 import Environment, FileSystemLoader

from config import SOURCE_ICONS
from sources.base import Item

TMPL_DIR = os.path.join(os.path.dirname(__file__), "templates")
_env = Environment(
    loader=FileSystemLoader(TMPL_DIR),
    autoescape=True,
)
_WEEKDAYS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]


def _domain(url: str) -> str:
    net = urlparse(url).netloc
    if net.startswith("www."):
        net = net[4:]
    return net


def _item_view(it: Item) -> dict:
    return {
        "key": it.key,
        "title": it.display_title,
        "url": it.url,
        "score_label": it.score_label,
        "extra": it.extra,
        "source": it.source,
        "source_label": it.source_label,
        "summary": it.summary,
        "tags": list(it.tags),
        "meta": it.meta,
        "trend": it.trend,
        "domain": _domain(it.url),
    }


def build_report(items_by_source, ai_result: dict,
                 today: datetime.date | None = None) -> dict:
    today = today or datetime.date.today()
    sources = []
    for src_key, label, src_items in items_by_source:
        sources.append({
            "key": src_key,
            "label": label,
            "icon": SOURCE_ICONS.get(src_key, "📌"),
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
