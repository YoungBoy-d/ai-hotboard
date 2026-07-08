import json

from ai_summarizer import summarize, build_prompt
from sources.base import Item


def _item(source, rank, title, description=""):
    return Item(source=source, source_label=source, rank=rank,
                title=title, url="u", description=description)


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
    prompt = build_prompt([_item("hackernews", 1, "GPT-5 released")])
    assert "[hackernews:1]" in prompt
    assert "GPT-5 released" in prompt


def test_build_prompt_includes_description():
    it = _item("arxiv", 1, "X", description="a novel method")
    assert "a novel method" in build_prompt([it])


def test_summarize_parses_items_structure():
    payload = {"editorial": [{"text": "AI 大爆发", "refs": ["hackernews:1"]}],
               "items": {"hackernews:1": {"zh": "GPT-5 发布",
                                          "summary": "OpenAI 新模型",
                                          "tags": ["LLM", "工具"]}}}
    result = summarize([_item("hackernews", 1, "GPT-5 released")],
                       client=FakeClient(json.dumps(payload)))
    assert result["editorial"][0]["text"] == "AI 大爆发"
    info = result["items"]["hackernews:1"]
    assert info["zh"] == "GPT-5 发布"
    assert info["summary"] == "OpenAI 新模型"
    assert info["tags"] == ["LLM", "工具"]


def test_summarize_normalizes_dirty_items():
    # 非字符串标签剔除、标签截断 3 个、缺失字段补空
    payload = {"editorial": [], "items": {"x:1": {"zh": "中", "summary": "解",
                                                   "tags": ["a", 1, "b", "c", "d"]}}}
    result = summarize([], client=FakeClient(json.dumps(payload)))
    info = result["items"]["x:1"]
    assert info["tags"] == ["a", "b", "c"]
    assert info["zh"] == "中"


def test_summarize_falls_back_on_exception():
    client = FakeClient("", exc=RuntimeError("api down"))
    result = summarize([_item("hackernews", 1, "x")], client=client)
    assert result == {"editorial": [], "items": {}}
