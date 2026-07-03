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
