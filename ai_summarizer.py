import json

from openai import OpenAI

from config import DASHSCOPE_API_KEY, DASHSCOPE_BASE_URL, QWEN_MODEL


def build_prompt(items) -> str:
    lines = []
    for it in items:
        desc = f" | {it.description}" if it.description else ""
        lines.append(f"[{it.key}] ({it.source_label}) {it.title}{desc}")
    catalog = "\n".join(lines)
    return f"""下面是今日 AI 技术热点的条目（[key] 为编号，| 后为简介/摘要）：

{catalog}

请完成两件事，严格以 JSON 返回：
1. editorial：3-5 条"今日要点"，每条形如 {{"text":"一句话中文摘要","refs":["key1",...]}}，refs 引用上面的编号。
2. items：为【每个 key】生成 {{"zh":"简短中文标题","summary":"1-2 句说人话的中文解读，讲清它是什么 / 为什么重要 / 对开发者意味着什么","tags":["标签1","标签2"]}}。标签 1-3 个，从 LLM/Agent/RAG/开源/CV/语音/论文/工具/资讯/变现 等里选。已经是中文的条目 zh 留空字符串。

只输出 JSON，不要任何解释或多余文字。格式：
{{"editorial":[...],"items":{{"key1":{{"zh":"","summary":"","tags":[]}}}}}}"""


def summarize(items, client=None) -> dict:
    """返回 {"editorial": [...], "items": {key: {zh, summary, tags}}}；任何失败都兜底为空。"""
    if client is None:
        if not DASHSCOPE_API_KEY:
            print("[ai] 未配置 DASHSCOPE_API_KEY，跳过摘要")
            return {"editorial": [], "items": {}}
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
        items_out = data.get("items", {}) or {}
        # 规范化：保证每个 key 的值是 dict，且字段齐全
        norm = {}
        for k, v in items_out.items():
            if not isinstance(v, dict):
                continue
            norm[k] = {
                "zh": (v.get("zh") or "").strip(),
                "summary": (v.get("summary") or "").strip(),
                "tags": [t for t in (v.get("tags") or []) if isinstance(t, str)][:3],
            }
        return {
            "editorial": data.get("editorial", []) or [],
            "items": norm,
        }
    except Exception as e:  # noqa: BLE001
        print(f"[ai] 摘要失败，使用兜底: {e}")
        return {"editorial": [], "items": {}}
