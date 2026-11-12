from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session, desc, select

from app.content.domains import domain_for
from app.content.search import (
    MODES,
    build_query,
    build_search_url,
    quote_term,
    terms_for_domain,
    terms_for_topic,
)
from app.database import get_session
from app.features.content_studio.models import ContentItem
from app.features.discovery.models import SavedSearch
from app.features.login.routes import require_login
from app.features.settings.models import get_profile
from app.web.templating import templates

router = APIRouter(dependencies=[Depends(require_login)])


def _search_card(mode_key: str, terms: list[str]) -> dict:
    config = MODES[mode_key]
    query = build_query(terms, mode_key)
    return {
        "mode": mode_key,
        "label": config["label"],
        "hint": config["hint"],
        "query": query,
        "url": build_search_url(query),
    }


def _topic_searches(session: Session, domain_key: str, limit: int = 3) -> list[dict]:
    query = (
        select(ContentItem)
        .where(ContentItem.domain == domain_key)
        .order_by(desc(ContentItem.created_at))
        .limit(limit)
    )
    searches = []
    for item in session.exec(query):
        terms = terms_for_topic(item.topic)
        searches.append(
            {
                "label": item.topic,
                "url": build_search_url(build_query(terms, "conversations")),
            }
        )
    return searches


@router.get("/discovery")
def discovery(
    request: Request,
    terms: str = "",
    mode: str = "conversations",
    session: Session = Depends(get_session),
):
    profile = get_profile(session)
    mode = mode if mode in MODES else "conversations"
    cards = []
    for domain in profile.domains():
        cards.append(
            {
                "domain": domain,
                "searches": [
                    _search_card(key, terms_for_domain(domain.search_terms)) for key in MODES
                ],
                "topics": _topic_searches(session, domain.key),
            }
        )

    custom = None
    if terms.strip():
        custom_terms = [quote_term(terms.strip())]
        query = build_query(custom_terms, mode)
        custom = {"query": query, "url": build_search_url(query)}

    saved = list(session.exec(select(SavedSearch).order_by(desc(SavedSearch.created_at))))
    return templates.TemplateResponse(
        request,
        "discovery.html",
        {
            "cards": cards,
            "modes": MODES,
            "saved": saved,
            "custom": custom,
            "terms": terms,
            "active_mode": mode,
            "domain_for": domain_for,
        },
    )


@router.post("/discovery/saved")
def save_search(
    label: str = Form(...),
    query: str = Form(...),
    domain: str = Form(""),
    session: Session = Depends(get_session),
):
    if query.strip():
        session.add(SavedSearch(label=label.strip()[:120] or "Search", query=query.strip(), domain=domain))
        session.commit()
    return RedirectResponse("/discovery", status_code=303)


@router.post("/discovery/saved/{search_id}/delete")
def delete_search(search_id: int, session: Session = Depends(get_session)):
    saved = session.get(SavedSearch, search_id)
    if saved is not None:
        session.delete(saved)
        session.commit()
    return RedirectResponse("/discovery", status_code=303)
