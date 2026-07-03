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
