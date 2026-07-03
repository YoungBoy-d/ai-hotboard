from dataclasses import dataclass


@dataclass
class Item:
    source: str            # 源标识，如 "hackernews"
    source_label: str      # 展示名，如 "Hacker News"
    rank: int              # 源内排名 1..N（由 safe_fetch 赋值）
    title: str             # 原始标题
    url: str               # 原文链接
    score: int = 0         # 热度数值（用于排序/参考）
    score_label: str = ""  # 热度展示文案，如 "▲ 123"
    extra: str = ""        # 附加信息（语言/作者/子源等）
    title_zh: str = ""     # AI 中文化标题；为空时展示用 title

    @property
    def key(self) -> str:
        return f"{self.source}:{self.rank}"

    @property
    def display_title(self) -> str:
        return self.title_zh or self.title


class BaseFetcher:
    source: str = ""
    source_label: str = ""

    def fetch(self, limit: int = 5) -> list[Item]:
        raise NotImplementedError

    def safe_fetch(self, limit: int = 5) -> list[Item]:
        """容错抓取：异常返回空列表，截断到 limit 并重排 rank。"""
        try:
            items = self.fetch(limit) or []
        except Exception as e:  # noqa: BLE001
            print(f"[{self.source}] 获取失败: {e}")
            return []
        items = items[:limit]
        for i, it in enumerate(items):
            it.rank = i + 1
        return items
