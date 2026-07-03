from sources.base import Item, BaseFetcher


def test_item_key_and_display_title():
    it = Item(source="hackernews", source_label="Hacker News", rank=2,
              title="Hello AI", url="https://x.com")
    assert it.key == "hackernews:2"
    assert it.display_title == "Hello AI"  # title_zh 为空时回退原标题


def test_item_display_title_prefers_zh():
    it = Item(source="v2ex", source_label="V2EX", rank=1, title="abc",
              url="u", title_zh="中文化标题")
    assert it.display_title == "中文化标题"


def test_safe_fetch_assigns_rank_and_handles_error():
    class Boom(BaseFetcher):
        source = "x"
        source_label = "X"
        def fetch(self, limit=5):
            raise RuntimeError("boom")

    class Ok(BaseFetcher):
        source = "y"
        source_label = "Y"
        def fetch(self, limit=5):
            return [Item(source="y", source_label="Y", rank=0, title=f"t{i}", url="u")
                    for i in range(8)]

    assert Boom().safe_fetch(5) == []           # 异常 → 空列表，不抛
    ok = Ok().safe_fetch(5)
    assert [i.rank for i in ok] == [1, 2, 3, 4, 5]  # 截断 + 重排 rank
