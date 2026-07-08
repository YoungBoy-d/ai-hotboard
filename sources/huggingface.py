import requests

from config import REQUEST_HEADERS, REQUEST_TIMEOUT
from sources.base import BaseFetcher, Item

HF_API = "https://huggingface.co/api/models"

# pipeline_tag → 友好展示标签
_TASK_LABELS = {
    "text-generation": "LLM", "text2text-generation": "LLM",
    "conversational": "LLM", "fill-mask": "NLP",
    "token-classification": "NLP", "question-answering": "NLP",
    "summarization": "NLP", "translation": "NLP",
    "image-classification": "CV", "object-detection": "CV",
    "image-segmentation": "CV", "text-to-image": "CV·生成",
    "automatic-speech-recognition": "语音", "text-to-speech": "语音",
    "feature-extraction": "嵌入", "sentence-similarity": "嵌入",
}


def _human(n: int) -> str:
    """1234567 → '1.2M'；3400 → '3.4k'；580 → '580'。"""
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}k"
    return str(n)


class HuggingFaceFetcher(BaseFetcher):
    source = "hf"
    source_label = "HuggingFace 模型"

    def fetch(self, limit: int = 5) -> list[Item]:
        # 官方 API 的 sort 取值各实例支持不一：先试 trending（最贴"趋势"），
        # 若被拒(400)则降级 likes（热门模型）。其它错误向上抛由 safe_fetch 兜底。
        params = {"limit": max(limit * 4, 30)}
        last_exc = None
        for sort in ("trending", "likes"):
            try:
                resp = requests.get(HF_API, params={**params, "sort": sort},
                                    headers=REQUEST_HEADERS, timeout=REQUEST_TIMEOUT)
                resp.raise_for_status()
                return parse_hf(resp.json(), limit, self.source, self.source_label)
            except requests.HTTPError as e:  # noqa: PERF203
                if e.response is not None and e.response.status_code == 400:
                    continue
                last_exc = e
        if last_exc:
            raise last_exc
        return []



def parse_hf(data: list, limit: int = 5,
             source: str = "hf", source_label: str = "HuggingFace 模型") -> list[Item]:
    items: list[Item] = []
    for m in data[:limit]:
        mid = m.get("id", "") or ""
        if not mid:
            continue
        downloads = m.get("downloads", 0) or 0
        likes = m.get("likes", 0) or 0
        task = m.get("pipeline_tag", "") or ""
        tags_raw = m.get("tags", []) or []
        author = mid.split("/")[0] if "/" in mid else ""
        library = m.get("library_name", "") or ""

        license_ = ""
        for t in tags_raw:
            if isinstance(t, str) and t.startswith("license:"):
                license_ = t.split(":", 1)[1]
                break

        chips = []
        if task:
            chips.append(_TASK_LABELS.get(task, task))
        chips.append("开源")

        desc_parts = [p for p in [task, library, f"license:{license_}"] if p]
        meta_parts = [p for p in [f"作者 · {author}" if author else "",
                                  f"框架 · {library}" if library else "",
                                  f"许可 · {license_}" if license_ else ""] if p]

        items.append(Item(
            source=source, source_label=source_label, rank=0,
            title=mid,
            url=f"https://huggingface.co/{mid}",
            score=downloads,
            score_label=f"⬇ {_human(downloads)} · 👍 {_human(likes)}",
            extra="",
            description=" · ".join(desc_parts),
            tags=chips,
            meta="  ·  ".join(meta_parts),
        ))
    return items
