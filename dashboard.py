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
