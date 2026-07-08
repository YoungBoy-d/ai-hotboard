from sources.huggingface import parse_hf, _human


def test_human_formats_big_numbers():
    assert _human(580) == "580"
    assert _human(3400) == "3.4k"
    assert _human(1234567) == "1.2M"


def test_parse_hf_extracts_full_detail():
    data = [{
        "id": "Qwen/Qwen3-235B",
        "downloads": 1234567,
        "likes": 3400,
        "pipeline_tag": "text-generation",
        "library_name": "transformers",
        "tags": ["transformers", "safetensors", "license:apache-2.0"],
    }]
    items = parse_hf(data, limit=5)
    assert len(items) == 1
    it = items[0]
    assert it.title == "Qwen/Qwen3-235B"
    assert it.url == "https://huggingface.co/Qwen/Qwen3-235B"
    assert "1.2M" in it.score_label and "3.4k" in it.score_label
    assert "LLM" in it.tags          # pipeline_tag → LLM
    assert "开源" in it.tags
    assert "作者 · Qwen" in it.meta
    assert "框架 · transformers" in it.meta
    assert "许可 · apache-2.0" in it.meta
    assert "text-generation" in it.description


def test_parse_hf_skips_empty_id():
    items = parse_hf([{"id": "", "downloads": 1}, {"id": "org/m"}], limit=5)
    assert [i.title for i in items] == ["org/m"]


def test_parse_hf_respects_limit():
    data = [{"id": f"o/r{i}", "downloads": i} for i in range(10)]
    assert len(parse_hf(data, limit=3)) == 3
