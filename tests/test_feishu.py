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
