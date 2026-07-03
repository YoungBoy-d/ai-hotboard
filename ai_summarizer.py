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
