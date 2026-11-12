"""Deciding what to write about on a given day.

Pure functions, no database and no AI, so the plan can be tested directly.
"""

from dataclasses import dataclass
from datetime import date
from itertools import count as _count

from app.content.domains import BASE_FORMATS, Domain


@dataclass(frozen=True)
class PlanItem:
    domain: Domain
    discipline: str
    topic: str
    post_format: str


def _pick_topic(domain: Domain, offset: int, recent_topics: set[str]) -> str:
    topics = domain.topics
    for step in range(len(topics)):
        candidate = topics[(offset + step) % len(topics)]
        if candidate.casefold() not in recent_topics:
            return candidate
    return topics[offset % len(topics)]


def build_plan(
    domains: list[Domain],
    count: int,
    today: date,
    recent_topics: set[str] | None = None,
    include_threads: bool = True,
) -> list[PlanItem]:
    """Spread `count` posts across domains, disciplines and formats.

    Offsets come from the date so the sequence changes every day, and the
    starting domain rotates so a three-post day still visits every domain
    over the course of a week.
    """
    if not domains or count <= 0:
        return []

    recent = {topic.casefold() for topic in (recent_topics or set())}
    ordinal = today.toordinal()
    start = ordinal % len(domains)
    formats = list(BASE_FORMATS)
    plan: list[PlanItem] = []

    for position in _count():
        if position >= count:
            break
        domain = domains[(start + position) % len(domains)]
        discipline = domain.disciplines[(ordinal + position) % len(domain.disciplines)]
        post_format = formats[(ordinal + position) % len(formats)]
        if include_threads and count >= 3 and position == 1:
            post_format = "thread"
        topic = _pick_topic(domain, ordinal + position, recent)
        plan.append(PlanItem(domain=domain, discipline=discipline, topic=topic, post_format=post_format))

    return plan


def interleave_ai_topics(plan: list[PlanItem], ideas: list[str]) -> list[PlanItem]:
    """Replace plan topics with AI ideas, keeping the domain/format skeleton.

    Ideas are matched to plan items in order. Extra or missing ideas are
    harmless: anything unmatched keeps its seed topic.
    """
    if not ideas:
        return plan
    updated = []
    for position, item in enumerate(plan):
        if position < len(ideas):
            idea = ideas[position].strip().strip('"')
            if 8 <= len(idea) <= 160:
                item = PlanItem(item.domain, item.discipline, idea, item.post_format)
        updated.append(item)
    return updated
