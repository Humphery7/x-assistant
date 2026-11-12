from pathlib import Path

from fastapi.templating import Jinja2Templates

WEB_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=WEB_DIR / "templates")
templates.env.globals["nav_items"] = [
    {"label": "Overview", "path": "/"},
    {"label": "Content Studio", "path": "/content"},
    {"label": "Discussion Discovery", "path": "/discovery"},
    {"label": "Saved Discussions", "path": "/discussions"},
    {"label": "Engagement Assistant", "path": "/replies"},
    {"label": "Analytics", "path": "/analytics"},
    {"label": "Settings", "path": "/settings"},
]
