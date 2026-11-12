"""X advanced-search links, built locally. No API, no cost.

X search is a URL: https://x.com/search?q=<query>&src=typed_query&f=live
The query supports operators like min_faves:, lang:, since:, filter:links and
-filter:replies. We build those queries so discovery is one click.
"""

from datetime import date, timedelta
from urllib.parse import urlencode

STOPWORDS = {
    "a", "an", "the", "is", "are", "was", "were", "be", "been", "being",
    "why", "what", "how", "when", "where", "which", "who", "whom",
    "your", "you", "our", "we", "they", "them", "their", "it", "its",
    "to", "of", "and", "or", "in", "on", "for", "with", "that", "this",
    "these", "those", "from", "at", "as", "by", "into", "than", "then",
    "not", "do", "does", "did", "can", "could", "should", "would",
    "more", "most", "less", "much", "actually", "still", "just", "only",
    "every", "once", "also", "very", "really", "about", "after", "before",
    "worse", "better", "real", "thing", "things", "people", "everyone",
    "nobody", "something", "anything", "without", "because", "makes", "make",
}

CONVERSATION_SIGNALS = (
    '"lessons learned"', '"we built"', '"the tradeoff"', '"in practice"',
    "how", "why", '"what changed"',
)

PROBLEM_SIGNALS = (
    '"anyone else"', '"how do you"', '"what am I missing"', "struggling",
    '"keeps failing"', "debugging", '"root cause"',
)

BREAKTHROUGH_SIGNALS = (
    "paper", '"we shipped"', "benchmark", '"open sourced"', "breakthrough",
    '"what this changes"',
)

MODES: dict[str, dict[str, object]] = {
    "conversations": {
        "label": "Live conversations",
        "hint": "People already arguing about the trade-offs.",
        "signals": CONVERSATION_SIGNALS,
        "min_faves": 15,
    },
    "problems": {
        "label": "Problems in the wild",
        "hint": "Engineers stuck on something you may have solved.",
        "signals": PROBLEM_SIGNALS,
        "min_faves": 5,
    },
    "breakthroughs": {
        "label": "Breakthroughs & papers",
        "hint": "New results, launches and benchmarks worth reacting to.",
        "signals": BREAKTHROUGH_SIGNALS,
        "min_faves": 20,
    },
}


def keywords(text: str, limit: int = 4) -> list[str]:
    words = []
    for raw in text.replace("/", " ").replace("-", " ").split():
        word = raw.strip(".,:;!?()[]{}\"'").lower()
        if len(word) < 3 or word in STOPWORDS or word.isdigit():
            continue
        if word not in words:
            words.append(word)
    return words[:limit]


def terms_for_topic(topic: str) -> list[str]:
    found = keywords(topic)
    return found or [topic.strip()]


def terms_for_domain(search_terms: tuple[str, ...]) -> list[str]:
    return [f'"{term}"' if " " in term else term for term in search_terms]


def build_query(
    terms: list[str],
    mode: str = "conversations",
    since: date | None = None,
    days: int = 7,
) -> str:
    config = MODES.get(mode, MODES["conversations"])
    signals = " OR ".join(config["signals"])  # type: ignore[arg-type]
    topic_block = " OR ".join(terms)
    since_date = since or date.today()
    start = since_date - timedelta(days=days)
    parts = [
        f"({topic_block})",
        f"({signals})",
        f"min_faves:{config['min_faves']}",
        "lang:en",
        f"since:{start.isoformat()}",
        "-filter:replies",
    ]
    if mode == "breakthroughs":
        parts.append("filter:links")
    return " ".join(parts)


def build_search_url(query: str) -> str:
    params = urlencode({"q": query, "src": "typed_query", "f": "live"})
    return f"https://x.com/search?{params}"


def search_link(terms: list[str], mode: str = "conversations", days: int = 7) -> str:
    return build_search_url(build_query(terms, mode, days=days))


def quote_term(term: str) -> str:
    return f'"{term}"' if " " in term else term


# quote_term is part of the public surface: routes use it for free-text terms.
__all__ = [
    "MODES", "build_query", "build_search_url", "keywords",
    "quote_term", "search_link", "terms_for_domain", "terms_for_topic",
]
