from sources.arxiv import parse_arxiv

ATOM = b"""<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
<entry>
  <id>http://arxiv.org/abs/2401.12345v1</id>
  <title>Long Context Attention Compression</title>
  <summary>We propose a lossless compression method for 1M token context.</summary>
  <published>2026-07-01T00:00:00Z</published>
  <author><name>Alice</name></author>
  <author><name>Bob</name></author>
  <link href="http://arxiv.org/abs/2401.12345v1" rel="alternate" type="text/html"/>
  <category term="cs.CL"/>
</entry>
<entry>
  <id>http://arxiv.org/abs/2401.99999v1</id>
  <title>Vision Language Model Survey</title>
  <summary>A survey of VLMs.</summary>
  <published>2026-07-02T00:00:00Z</published>
  <author><name>Carol</name></author>
  <link href="http://arxiv.org/abs/2401.99999v1" rel="alternate" type="text/html"/>
  <category term="cs.CV"/>
</entry>
</feed>"""


def test_parse_arxiv_extracts_full_detail():
    items = parse_arxiv(ATOM, limit=5)
    assert len(items) == 2
    it = items[0]
    assert it.title == "Long Context Attention Compression"
    assert it.url == "http://arxiv.org/abs/2401.12345v1"
    assert "lossless" in it.description
    assert "论文" in it.tags and "NLP" in it.tags   # cs.CL → NLP
    assert "Alice" in it.meta and "Bob" in it.meta
    assert "PDF" in it.meta
    assert "2026-07-01" in it.meta
    assert it.extra == "cs.CL"
    assert it.score_label == ""                      # arXiv 无热度指标


def test_parse_arxiv_respects_limit():
    items = parse_arxiv(ATOM, limit=1)
    assert len(items) == 1


def test_parse_arxiv_empty_feed():
    assert parse_arxiv(b"<?xml version='1.0'?><feed xmlns='http://www.w3.org/2005/Atom'/>", limit=5) == []
