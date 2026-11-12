from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, desc, func, select

from app.background_jobs.job_run_log import JobRun
from app.content.domains import domain_for, label_for_format
from app.database import get_session
from app.features.content_studio.models import ContentItem, ContentStatus, ThreadPost
from app.features.discussions.models import Discussion, DiscussionStatus, Reply, ReplyStatus
from app.features.login.routes import require_login
from app.web.templating import templates

router = APIRouter(dependencies=[Depends(require_login)])


def _count(session: Session, model, *where) -> int:
    query = select(func.count()).select_from(model)
    for clause in where:
        query = query.where(clause)
    return session.exec(query).one()


@router.get("/analytics")
def analytics(request: Request, session: Session = Depends(get_session)):
    by_status = dict(
        session.exec(select(ContentItem.status, func.count()).group_by(ContentItem.status)).all()
    )
    by_domain = dict(
        session.exec(select(ContentItem.domain, func.count()).group_by(ContentItem.domain)).all()
    )
    by_format = dict(
        session.exec(select(ContentItem.post_format, func.count()).group_by(ContentItem.post_format)).all()
    )

    total_content = sum(by_status.values())
    published = by_status.get(ContentStatus.PUBLISHED, 0)
    approved = by_status.get(ContentStatus.APPROVED, 0)
    drafts = by_status.get(ContentStatus.DRAFT, 0)
    threads = len(session.exec(select(ThreadPost.content_item_id).distinct()).all())
    discussions = _count(session, Discussion)
    replies = _count(session, Reply)
    replies_published = _count(session, Reply, Reply.status == ReplyStatus.PUBLISHED)
    discussions_replied = _count(session, Discussion, Discussion.status == DiscussionStatus.REPLIED)

    since = datetime.now(timezone.utc) - timedelta(days=14)
    runs = list(
        session.exec(select(JobRun).where(JobRun.started_at >= since).order_by(desc(JobRun.started_at)))
    )
    success = len([run for run in runs if run.status == "completed"])
    failures = len([run for run in runs if run.status == "failed"])

    figure = lambda label, value: {"label": label, "value": value}  # noqa: E731
    figures = [
        figure("Posts generated", total_content),
        figure("Published", published),
        figure("Discussions saved", discussions),
        figure("Replies generated", replies),
    ]

    review_funnel = [
        {"label": "Awaiting review", "value": drafts, "hint": "Drafts waiting on you."},
        {"label": "Approved", "value": approved, "hint": "Cleared to publish by hand."},
        {"label": "Published", "value": published, "hint": "Marked as live on X."},
        {"label": "Threads", "value": threads, "hint": "Multi-post content."},
    ]

    domain_rows = [
        {
            "name": domain_for(key).name,
            "value": value,
            "share": round(100 * value / total_content) if total_content else 0,
        }
        for key, value in sorted(by_domain.items(), key=lambda row: row[1], reverse=True)
    ]
    format_rows = [
        {
            "name": label_for_format(key),
            "value": value,
            "share": round(100 * value / total_content) if total_content else 0,
        }
        for key, value in sorted(by_format.items(), key=lambda row: row[1], reverse=True)
    ]

    return templates.TemplateResponse(
        request,
        "analytics.html",
        {
            "figures": figures,
            "review_funnel": review_funnel,
            "domain_rows": domain_rows,
            "format_rows": format_rows,
            "discussions_replied": discussions_replied,
            "replies_published": replies_published,
            "runs_total": len(runs),
            "runs_success": success,
            "runs_failed": failures,
            "runs": runs[:10],
        },
    )
