from datetime import date, timedelta

from app.content.domains import DOMAINS
from app.content.plan import build_plan, interleave_ai_topics

DOMAINS_LIST = list(DOMAINS.values())


def test_plan_has_the_requested_count_and_valid_fields():
    plan = build_plan(DOMAINS_LIST, count=3, today=date(2026, 11, 12))
    assert len(plan) == 3
    for item in plan:
        assert item.topic in item.domain.topics
        assert item.discipline in item.domain.disciplines
        assert item.post_format


def test_plan_includes_a_thread_when_enabled():
    plan = build_plan(DOMAINS_LIST, count=3, today=date(2026, 11, 12), include_threads=True)
    assert "thread" in [item.post_format for item in plan]


def test_plan_has_no_threads_when_disabled():
    plan = build_plan(DOMAINS_LIST, count=3, today=date(2026, 11, 12), include_threads=False)
    assert "thread" not in [item.post_format for item in plan]


def test_plan_visits_every_domain_over_a_week():
    seen = set()
    for offset in range(7):
        plan = build_plan(
            DOMAINS_LIST, count=3, today=date(2026, 11, 12) + timedelta(days=offset)
        )
        seen.update(item.domain.key for item in plan)
    assert seen == set(DOMAINS.keys())


def test_plan_skips_recent_topics():
    first = build_plan(DOMAINS_LIST, count=1, today=date(2026, 11, 12))[0]
    second = build_plan(
        DOMAINS_LIST, count=1, today=date(2026, 11, 12), recent_topics={first.topic}
    )[0]
    assert second.topic != first.topic


def test_ai_ideas_replace_topics_but_keep_the_skeleton():
    plan = build_plan(DOMAINS_LIST, count=2, today=date(2026, 11, 12))
    updated = interleave_ai_topics(plan, ["A specific idea about chiplets"])
    assert updated[0].topic == "A specific idea about chiplets"
    assert updated[0].domain == plan[0].domain
    assert updated[0].post_format == plan[0].post_format
    assert updated[1].topic == plan[1].topic


def test_junk_ai_ideas_are_ignored():
    plan = build_plan(DOMAINS_LIST, count=1, today=date(2026, 11, 12))
    updated = interleave_ai_topics(plan, ["short"])
    assert updated[0].topic == plan[0].topic
