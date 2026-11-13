import secrets
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.database import create_tables
from app.features.analytics import routes as analytics_routes
from app.features.content_studio import routes as content_routes
from app.features.discussions import routes as discussion_routes
from app.features.discovery import routes as discovery_routes
from app.features.login import routes as login_routes
from app.features.overview import routes as overview_routes
from app.features.settings import routes as settings_routes
from app.settings import load_settings
from app.web.templating import WEB_DIR

settings = load_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    yield


app = FastAPI(title="X Assistant", lifespan=lifespan)
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.session_secret or secrets.token_hex(32),
    same_site="lax",
    https_only=settings.secure_cookies,
)
app.mount("/static", StaticFiles(directory=WEB_DIR / "static"), name="static")


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return FileResponse(WEB_DIR / "static" / "favicon.ico")


app.include_router(login_routes.router)
app.include_router(overview_routes.router)
app.include_router(content_routes.router)
app.include_router(discovery_routes.router)
app.include_router(discussion_routes.router)
app.include_router(analytics_routes.router)
app.include_router(settings_routes.router)
