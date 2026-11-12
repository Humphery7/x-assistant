from datetime import date, timedelta
from typing import Optional

from sqlmodel import Session, desc, select

from app.ai.prompts import (
    Voice,
    build_post_prompt,
    build_topic_prompt,
    clean_post_text,
    parse_topic_ideas,
    split_thread,
)
from app.ai.provider import AiProvider
from app.background_jobs.job_run_log import JobRun, already_completed, logged_job_run
from app.content.plan import build_plan, interleave_ai_topics
from app.features.content_studio.models import (
    ContentItem,
    ContentSource,
    ContentStatus,
    ThreadPost,
)
from app.features.settings.models import get_profile

JOB_NAME = "daily_content"
POSTS_PER_DAY = 3


def _recent_posts(session: Session, limit: int = 10) -> list[str]:
    query = select(ContentItem).order_by(desc(ContentItem.created_at)).limit(limit)
    return [f"{item.topic}: {item.body[:110]}" for item in session.exec(query)]


def _recent_topics(session: Session, days: int = 14) -> set[str]:
    cutoff = date.today() - timedelta(days=days)
    query = (
        select(ContentItem.topic)
        .where(ContentItem.scheduled_for >= cutoff)
        .order_by(desc(ContentItem.created_at))
        .limit(40)
    )
    return {topic for topic in session.exec(query)}


def _discover_topics(ai: AiProvider, plan, voice: Voice, recent: set[str]) -> list[str]:
    """One ideation call for the whole day. Seeds are the fallback."""
    domains = []
    for item in plan:
        if item.domain not in domains:
            domains.append(item.domain)
    prompt = build_topic_prompt(
        domains=domains, count=len(plan), voice=voice, recent_topics=sorted(recent)
    )
    try:
        return parse_topic_ideas(ai.generate_text(prompt))
    except Exception:
        # Ideation is a nice-to-have; the curated seed topics are the fallback.
        return []


def run_daily_content_job(session: Session, ai: AiProvider, today: Optional[date] = None) -> Optional[JobRun]:
    today = today or date.today()
    if already_completed(session, JOB_NAME, today):
        return None
    with logged_job_run(session, JOB_NAME, today) as run:
        profile = get_profile(session)
        voice = Voice.from_profile(profile)
        recent_topics = _recent_topics(session)
        plan = build_plan(
            domains=profile.domains(),
            count=profile.posts_per_day,
            today=today,
            recent_topics=recent_topics,
            include_threads=profile.include_threads,
        )
        plan = interleave_ai_topics(plan, _discover_topics(ai, plan, voice, recent_topics))
        recent = _recent_posts(session)

        for item in plan:
            prompt = build_post_prompt(
                topic=item.topic,
                discipline=item.discipline,
                domain=item.domain,
                post_format=item.post_format,
                voice=voice,
                recent=recent,
            )
            body = clean_post_text(ai.generate_text(prompt))
            content = ContentItem(
                domain=item.domain.key,
                discipline=item.discipline,
                topic=item.topic,
                post_format=item.post_format,
                body=body,
                status=ContentStatus.DRAFT,
                source=ContentSource.DAILY_JOB,
                scheduled_for=today,
            )
            session.add(content)
            session.flush()

            if item.post_format == "thread":
                posts = split_thread(body)
                if len(posts) > 1:
                    for position, post in enumerate(posts):
                        session.add(ThreadPost(content_item_id=content.id, position=position, body=post))

            run.items_created += 1
        session.commit()
    return run
