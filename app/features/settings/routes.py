from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlmodel import Session

from app.content.domains import all_domains
from app.database import get_session
from app.features.login.routes import require_login
from app.features.settings.models import get_profile, save_profile
from app.settings import load_settings
from app.web.templating import templates

router = APIRouter(dependencies=[Depends(require_login)])


@router.get("/settings")
def settings_page(request: Request, saved: bool = False, session: Session = Depends(get_session)):
    profile = get_profile(session)
    return templates.TemplateResponse(
        request,
        "settings.html",
        {
            "profile": profile,
            "domains": all_domains(),
            "selected": set(profile.domain_keys()) or {domain.key for domain in all_domains()},
            "ai_ready": bool(load_settings().gemini_api_key),
            "saved": saved,
        },
    )


@router.post("/settings")
def settings_save(
    domains: list[str] = Form(default=[]),
    interests: str = Form(""),
    style_notes: str = Form(""),
    voice_samples: str = Form(""),
    avoid: str = Form(""),
    posts_per_day: int = Form(3),
    include_threads: str | None = Form(None),
    session: Session = Depends(get_session),
):
    save_profile(
        session,
        domain_keys=[domain.key for domain in all_domains() if domain.key in domains],
        interests=interests,
        style_notes=style_notes,
        voice_samples=voice_samples,
        avoid=avoid,
        posts_per_day=posts_per_day,
        include_threads=include_threads is not None,
    )
    return RedirectResponse("/settings?saved=true", status_code=303)
