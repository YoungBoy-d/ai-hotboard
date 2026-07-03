from sources.github_trending import parse_trending

FIXTURE = """
<section><article class="Box-row">
  <h2><a href="/owner/repo-a">repo-a</a></h2>
  <span itemprop="programmingLanguage">Python</span>
  <a class="Link Link--muted" href="/owner/repo-a/stargazers">100</a>
  <span class="d-inline-block float-sm-right">12 stars today</span>
</article>
<article class="Box-row">
  <h2><a href="/owner/repo-b">repo-b</a></h2>
  <a class="Link Link--muted" href="/owner/repo-b/stargazers">50</a>
</article></section>
"""


def test_parse_trending_extracts_repo_lang_and_stars():
    items = parse_trending(FIXTURE, limit=5)
    assert [i.title for i in items] == ["owner/repo-a", "owner/repo-b"]
    assert items[0].url == "https://github.com/owner/repo-a"
    assert items[0].extra == "Python"
    assert "12 stars today" in items[0].score_label
    # Missing language/today stars should not error
    assert items[1].extra == ""
