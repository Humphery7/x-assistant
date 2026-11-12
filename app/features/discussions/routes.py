from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, desc, select

from app.ai.prompts import (
    Voice,
    build_reply_followup_prompt,
    build_reply_prompt,
    parse_reply,
)
from app.ai.provider import get_ai_provider
from app.content.domains import all_domains, domain_for
from app.database import get_session
from app.features.discussions.models import Discussion, DiscussionStatus, Reply, ReplyStatus
from app.features.login.routes import require_login
from app.features.settings.models import get_profile
from app.settings import load_settings
from app.web.templating import templates

router = APIRouter(dependencies=[Depends(require_login)])

REPLY_ACTIONS = {
    "draft": ReplyStatus.DRAFT,
    "approve": ReplyStatus.APPROVED,
    "publish": ReplyStatus.PUBLISHED,
}


def _context(**extra) -> dict:
    base = {
        "domains": all_domains(),
        "domain_for": domain_for,
        "ai_ready": bool(load_settings().gemini_api_key),
    }
    base.update(extra)
    return base


def _get_discussion(session: Session, discussion_id: int) -> Discussion:
    discussion = session.get(Discussion, discussion_id)
    if discussion is None:
        raise HTTPException(status_code=404, detail="Discussion not found")
    return discussion


def _replies(session: Session, discussion_id: int) -> list[Reply]:
    query = (
        select(Reply)
        .where(Reply.discussion_id == discussion_id)
        .order_by(desc(Reply.created_at))
    )
    return list(session.exec(query))


@router.get("/discussions")
def discussions(request: Request, status: str = "", session: Session = Depends(get_session)):
    query = select(Discussion)
    if status:
        query = query.where(Discussion.status == status)
    rows = list(session.exec(query.order_by(desc(Discussion.created_at)).limit(200)))
    reply_counts = {}
    for discussion in rows:
        reply_counts[discussion.id] = len(_replies(session, discussion.id))
    return templates.TemplateResponse(
        request,
        "discussions.html",
        _context(discussions=rows, reply_counts=reply_counts, active_status=status),
    )


@router.get("/discussions/new")
def discussion_new(
    request: Request,
    url: str = "",
    title: str = "",
    domain: str = "software",
):
    return templates.TemplateResponse(
        request,
        "discussion_new.html",
        _context(url=url, title=title, selected_domain=domain),
    )


@router.post("/discussions/new")
def discussion_create(
    text: str = Form(...),
    url: str = Form(""),
    author: str = Form(""),
    title: str = Form(""),
    domain: str = Form("software"),
    notes: str = Form(""),
    session: Session = Depends(get_session),
):
    discussion = Discussion(
        url=url.strip(),
        author=author.strip(),
        title=title.strip() or (text.strip().splitlines()[0][:90] if text.strip() else "Untitled"),
        domain=domain if domain in {d.key for d in all_domains()} else "software",
        text=text.strip(),
        notes=notes.strip(),
    )
    session.add(discussion)
    session.commit()
    session.refresh(discussion)
    return RedirectResponse(f"/discussions/{discussion.id}", status_code=303)


@router.get("/discussions/{discussion_id}")
def discussion_detail(
    discussion_id: int,
    request: Request,
    error: str = "",
    session: Session = Depends(get_session),
):
    discussion = _get_discussion(session, discussion_id)
    return templates.TemplateResponse(
        request,
        "discussion_detail.html",
        _context(discussion=discussion, replies=_replies(session, discussion.id), error=error),
    )


@router.post("/discussions/{discussion_id}/replies")
def generate_reply(
    discussion_id: int,
    focus: str = Form(""),
    session: Session = Depends(get_session),
):
    discussion = _get_discussion(session, discussion_id)
    profile = get_profile(session)
    ai = get_ai_provider(load_settings())
    prompt = build_reply_prompt(
        discussion_text=discussion.text,
        author=discussion.author,
        url=discussion.url,
        discipline=discussion.domain,
        voice=Voice.from_profile(profile),
        focus=focus,
    )
    try:
        approach, body = parse_reply(ai.generate_text(prompt))
    except Exception as error:  # provider/runtime failures should not lose the page
        return RedirectResponse(
            f"/discussions/{discussion.id}?{urlencode({'error': str(error)})}", status_code=303
        )

    if not body:
        return RedirectResponse(
            f"/discussions/{discussion.id}?{urlencode({'error': 'The model returned an empty reply'})}",
            status_code=303,
        )
    session.add(Reply(discussion_id=discussion.id, body=body, approach=approach))
    discussion.status = DiscussionStatus.REPLIED
    session.add(discussion)
    session.commit()
    return RedirectResponse(f"/discussions/{discussion.id}", status_code=303)


@router.post("/discussions/{discussion_id}/status")
def discussion_status(
    discussion_id: int,
    action: str = Form(...),
    session: Session = Depends(get_session),
):
    discussion = _get_discussion(session, discussion_id)
    target = {
        "archive": DiscussionStatus.ARCHIVED,
        "save": DiscussionStatus.SAVED,
        "replied": DiscussionStatus.REPLIED,
    }.get(action)
    if target:
        discussion.status = target
        session.add(discussion)
        session.commit()
    return RedirectResponse(f"/discussions/{discussion.id}", status_code=303)


@router.post("/discussions/{discussion_id}/delete")
def discussion_delete(discussion_id: int, session: Session = Depends(get_session)):
    discussion = _get_discussion(session, discussion_id)
    for reply in _replies(session, discussion.id):
        session.delete(reply)
    session.delete(discussion)
    session.commit()
    return RedirectResponse("/discussions", status_code=303)


@router.get("/replies")
def replies_page(request: Request, status: str = "", session: Session = Depends(get_session)):
    query = select(Reply)
    if status:
        query = query.where(Reply.status == status)
    rows = list(session.exec(query.order_by(desc(Reply.created_at)).limit(200)))
    discussions = {d.id: d for d in session.exec(select(Discussion))}
    return templates.TemplateResponse(
        request,
        "replies.html",
        _context(replies=rows, discussions=discussions, active_status=status),
    )


@router.post("/replies/{reply_id}/status")
def reply_status(
    reply_id: int,
    action: str = Form(...),
    session: Session = Depends(get_session),
):
    reply = session.get(Reply, reply_id)
    if reply is None:
        raise HTTPException(status_code=404, detail="Reply not found")
    target = REPLY_ACTIONS.get(action)
    if target:
        reply.status = target
        session.add(reply)
        session.commit()
    return RedirectResponse(f"/discussions/{reply.discussion_id}", status_code=303)


@router.post("/replies/{reply_id}/rewrite")
def reply_rewrite(
    reply_id: int,
    note: str = Form(...),
    session: Session = Depends(get_session),
):
    reply = session.get(Reply, reply_id)
    if reply is None:
        raise HTTPException(status_code=404, detail="Reply not found")
    discussion = _get_discussion(session, reply.discussion_id)
    ai = get_ai_provider(load_settings())
    prompt = build_reply_followup_prompt(
        discussion_text=discussion.text, previous=reply.body, note=note
    )
    try:
        body = ai.generate_text(prompt).strip().strip('"')
    except Exception as error:
        return RedirectResponse(
            f"/discussions/{discussion.id}?{urlencode({'error': str(error)})}", status_code=303
        )
    if body:
        reply.body = body
        reply.status = ReplyStatus.DRAFT
        session.add(reply)
        session.commit()
    return RedirectResponse(f"/discussions/{discussion.id}", status_code=303)
