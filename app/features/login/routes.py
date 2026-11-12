import secrets

from fastapi import APIRouter, Form, HTTPException, Request
from fastapi.responses import RedirectResponse

from app.settings import load_settings
from app.web.templating import templates

router = APIRouter()


def require_login(request: Request) -> None:
    if not request.session.get("is_owner"):
        raise HTTPException(status_code=303, headers={"Location": "/login"})


@router.get("/login")
def login_page(request: Request):
    return templates.TemplateResponse(request, "login.html", {"error": None})


@router.post("/login")
def login(request: Request, password: str = Form(...)):
    owner_password = load_settings().owner_password
    if not owner_password:
        error = "OWNER_PASSWORD is not set on the server, so sign-in is disabled."
        return templates.TemplateResponse(request, "login.html", {"error": error}, status_code=503)
    if not secrets.compare_digest(password.encode(), owner_password.encode()):
        return templates.TemplateResponse(request, "login.html", {"error": "Wrong password."}, status_code=401)
    request.session["is_owner"] = True
    return RedirectResponse("/", status_code=303)


@router.post("/logout")
def logout(request: Request):
    request.session.clear()
    return RedirectResponse("/login", status_code=303)
