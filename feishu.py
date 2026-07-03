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
