from datetime import date
from urllib.parse import parse_qs, urlparse

from app.content.search import (
    MODES,
    build_query,
    build_search_url,
    keywords,
    terms_for_topic,
)


def test_keywords_drop_stopwords_and_duplicates():
    assert keywords("Why retries without jitter make outages worse, retries") == [
        "retries",
        "jitter",
        "outages",
    ]


def test_query_carries_the_advanced_search_operators():
    query = build_query(["chiplets", '"thermal design"'], "conversations", since=date(2026, 11, 12))
    assert 'min_faves:15' in query
    assert "lang:en" in query
    assert "-filter:replies" in query
    assert "since:2026-11-05" in query
    assert "(chiplets OR \"thermal design\")" in query


def test_breakthrough_searches_require_links():
    assert "filter:links" in build_query(["risc-v"], "breakthroughs")


def test_session_parameter_is_dropped_from_the_search_url():
    url = build_search_url(build_query(["firmware"], "problems"))
    parsed = urlparse(url)
    assert parsed.netloc == "x.com"
    assert parse_qs(parsed.query)["q"][0] == build_query(["firmware"], "problems")


def test_all_modes_have_a_label_and_signals():
    for key, config in MODES.items():
        assert config["label"] and config["signals"] and config["min_faves"], key


def test_topic_terms_stay_meaningful():
    terms = terms_for_topic("Why ground effect came back")
    assert "ground" in terms and "effect" in terms
    assert "why" not in terms
