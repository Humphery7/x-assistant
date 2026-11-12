from fastapi import APIRouter, Depends, Request
from sqlmodel import Session, desc, func, select

from app.background_jobs.job_run_log import JobRun
from app.content.domains import domain_for, label_for_format
from app.database import get_session
from app.features.content_studio.models import ContentItem, ContentStatus
from app.features.discussions.models import Discussion, DiscussionStatus, Reply, ReplyStatus
from app.features.login.routes import require_login
from app.features.settings.models import get_profile
from app.web.templating import templates

router = APIRouter(dependencies=[Depends(require_login)])


@router.get("/")
def overview(request: Request, session: Session = Depends(get_session)):
    counts = dict(session.exec(select(ContentItem.status, func.count()).group_by(ContentItem.status)).all())
    drafts = session.exec(
        select(ContentItem).where(ContentItem.status == ContentStatus.DRAFT)
        .order_by(desc(ContentItem.created_at)).limit(5)
    ).all()
    runs = session.exec(select(JobRun).order_by(desc(JobRun.started_at)).limit(5)).all()
    discussions = session.exec(
        select(Discussion).where(Discussion.status == DiscussionStatus.SAVED)
        .order_by(desc(Discussion.created_at)).limit(3)
    ).all()
    reply_count = session.exec(
        select(func.count()).select_from(Reply).where(Reply.status == ReplyStatus.DRAFT)
    ).one()
    profile = get_profile(session)
    figures = [
        ("Awaiting review", counts.get(ContentStatus.DRAFT, 0)),
        ("Approved", counts.get(ContentStatus.APPROVED, 0)),
        ("Published", counts.get(ContentStatus.PUBLISHED, 0)),
        ("Replies drafted", reply_count),
    ]
    return templates.TemplateResponse(
        request,
        "overview.html",
        {
            "figures": figures,
            "drafts": drafts,
            "runs": runs,
            "discussions": discussions,
            "profile": profile,
            "domain_for": domain_for,
            "label_for_format": label_for_format,
        },
    )
