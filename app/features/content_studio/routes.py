from datetime import date, datetime, timezone
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, delete, desc, func, select

from app.ai.prompts import Voice, build_post_prompt, clean_post_text, split_thread
from app.ai.provider import get_ai_provider
from app.content.domains import FORMAT_LABELS, all_domains, domain_for, label_for_format
from app.content.plan import PlanItem, build_plan
from app.database import get_session
from app.features.content_studio.models import (
    STATUS_LABELS,
    ContentItem,
    ContentSource,
    ContentStatus,
    ThreadPost,
)
from app.features.login.routes import require_login
from app.features.settings.models import get_profile
from app.settings import load_settings
from app.web.templating import templates

router = APIRouter(dependencies=[Depends(require_login)])

ACTION_STATUS = {
    "idea": ContentStatus.IDEA,
    "draft": ContentStatus.DRAFT,
    "approve": ContentStatus.APPROVED,
    "publish": ContentStatus.PUBLISHED,
    "reject": ContentStatus.REJECTED,
}


def _context(**extra) -> dict:
    base = {
        "domains": all_domains(),
        "format_labels": FORMAT_LABELS,
        "status_labels": STATUS_LABELS,
        "domain_for": domain_for,
        "label_for_format": label_for_format,
    }
    base.update(extra)
    return base


def _thread_posts(session: Session, item_id: int) -> list[ThreadPost]:
    query = (
        select(ThreadPost)
        .where(ThreadPost.content_item_id == item_id)
        .order_by(ThreadPost.position)
    )
    return list(session.exec(query))


def _replace_thread_posts(session: Session, item: ContentItem) -> None:
    session.exec(delete(ThreadPost).where(ThreadPost.content_item_id == item.id))
    posts = split_thread(item.body)
    if len(posts) < 2:
        return
    for position, post in enumerate(posts):
        session.add(ThreadPost(content_item_id=item.id, position=position, body=post))


def _get_item(session: Session, item_id: int) -> ContentItem:
    item = session.get(ContentItem, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Post not found")
    return item


@router.get("/content")
def content_list(
    request: Request,
    status: str = "",
    domain: str = "",
    session: Session = Depends(get_session),
):
    query = select(ContentItem)
    if status:
        query = query.where(ContentItem.status == status)
    if domain:
        query = query.where(ContentItem.domain == domain)
    items = list(session.exec(query.order_by(desc(ContentItem.created_at)).limit(200)))
    status_counts = dict(
        session.exec(select(ContentItem.status, func.count()).group_by(ContentItem.status)).all()
    )
    counts = {key: status_counts.get(key, 0) for key in STATUS_LABELS}
    return templates.TemplateResponse(
        request,
        "content_list.html",
        _context(items=items, active_status=status, active_domain=domain, counts=counts),
    )


@router.get("/content/new")
def content_new(request: Request):
    return templates.TemplateResponse(request, "content_new.html", _context())


@router.post("/content/new")
def content_create(
    topic: str = Form(...),
    body: str = Form(...),
    domain: str = Form("software"),
    discipline: str = Form(""),
    post_format: str = Form("short_insight"),
    angle: str = Form(""),
    session: Session = Depends(get_session),
):
    body = body.strip()
    if not body:
        raise HTTPException(status_code=400, detail="Post body cannot be empty")
    item = ContentItem(
        domain=domain if domain in {d.key for d in all_domains()} else "software",
        discipline=discipline.strip(),
        topic=topic.strip() or "Untitled",
        post_format=post_format if post_format in FORMAT_LABELS else "short_insight",
        body=body,
        angle=angle.strip(),
        status=ContentStatus.DRAFT,
        source=ContentSource.MANUAL,
    )
    session.add(item)
    session.flush()
    if item.post_format == "thread":
        _replace_thread_posts(session, item)
    session.commit()
    return RedirectResponse(f"/content/{item.id}", status_code=303)


@router.post("/content/generate")
def content_generate(
    domain: str = Form(""),
    post_format: str = Form(""),
    session: Session = Depends(get_session),
):
    profile = get_profile(session)
    domains = [item for item in profile.domains() if item.key == domain] or profile.domains()
    recent = [
        f"{item.topic}: {item.body[:110]}"
        for item in session.exec(select(ContentItem).order_by(desc(ContentItem.created_at)).limit(10))
    ]
    recent_topics = set(session.exec(select(ContentItem.topic).limit(40)))
    plan = build_plan(
        domains, count=1, today=date.today(), recent_topics=recent_topics, include_threads=False
    )
    chosen = plan[0]
    if post_format in FORMAT_LABELS:
        chosen = PlanItem(chosen.domain, chosen.discipline, chosen.topic, post_format)

    ai = get_ai_provider(load_settings())
    try:
        body = clean_post_text(
            ai.generate_text(
                build_post_prompt(
                    topic=chosen.topic,
                    discipline=chosen.discipline,
                    domain=chosen.domain,
                    post_format=chosen.post_format,
                    voice=Voice.from_profile(profile),
                    recent=recent,
                )
            )
        )
    except Exception as error:
        return RedirectResponse(
            f"/content?{urlencode({'error': str(error)[:300]})}", status_code=303
        )
    if not body:
        return RedirectResponse(
            f"/content?{urlencode({'error': 'The model returned an empty post'})}", status_code=303
        )

    item = ContentItem(
        domain=chosen.domain.key,
        discipline=chosen.discipline,
        topic=chosen.topic,
        post_format=chosen.post_format,
        body=body,
        status=ContentStatus.DRAFT,
        source=ContentSource.ON_DEMAND,
    )
    session.add(item)
    session.flush()
    if item.post_format == "thread":
        _replace_thread_posts(session, item)
    session.commit()
    return RedirectResponse(f"/content/{item.id}", status_code=303)


@router.get("/content/{item_id}")
def content_detail(item_id: int, request: Request, session: Session = Depends(get_session)):
    item = _get_item(session, item_id)
    return templates.TemplateResponse(
        request,
        "content_detail.html",
        _context(item=item, thread_posts=_thread_posts(session, item.id)),
    )


@router.post("/content/{item_id}/update")
def content_update(
    item_id: int,
    topic: str = Form(...),
    body: str = Form(...),
    domain: str = Form("software"),
    discipline: str = Form(""),
    post_format: str = Form("short_insight"),
    angle: str = Form(""),
    rationale: str = Form(""),
    session: Session = Depends(get_session),
):
    item = _get_item(session, item_id)
    item.topic = topic.strip() or item.topic
    item.body = body.strip() or item.body
    item.domain = domain if domain in {d.key for d in all_domains()} else item.domain
    item.discipline = discipline.strip()
    item.post_format = post_format if post_format in FORMAT_LABELS else item.post_format
    item.angle = angle.strip()
    item.rationale = rationale.strip()
    item.updated_at = datetime.now(timezone.utc)
    session.add(item)
    session.flush()
    _replace_thread_posts(session, item)
    session.commit()
    return RedirectResponse(f"/content/{item.id}", status_code=303)


@router.post("/content/{item_id}/status")
def content_status(
    item_id: int,
    action: str = Form(...),
    session: Session = Depends(get_session),
):
    item = _get_item(session, item_id)
    status = ACTION_STATUS.get(action)
    if status is None:
        raise HTTPException(status_code=400, detail="Unknown action")
    item.status = status
    item.updated_at = datetime.now(timezone.utc)
    if status == ContentStatus.PUBLISHED and item.published_at is None:
        item.published_at = datetime.now(timezone.utc)
    session.add(item)
    session.commit()
    return RedirectResponse(f"/content/{item.id}", status_code=303)


@router.post("/content/{item_id}/delete")
def content_delete(item_id: int, session: Session = Depends(get_session)):
    item = _get_item(session, item_id)
    session.exec(delete(ThreadPost).where(ThreadPost.content_item_id == item.id))
    session.delete(item)
    session.commit()
    return RedirectResponse("/content", status_code=303)
