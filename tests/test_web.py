from fastapi.testclient import TestClient
from sqlmodel import Session, SQLModel, create_engine
from sqlmodel.pool import StaticPool

from app.database import get_session
from app.features.content_studio import routes as content_routes
from app.features.discussions import routes as discussion_routes
from app.features.login.routes import require_login
from app.main import app

engine = create_engine(
    "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
)
SQLModel.metadata.create_all(engine)


class FakeAi:
    def generate_text(self, prompt: str) -> str:
        return "APPROACH: add a concrete measurement\nREPLY: We measured 12% at 85C and it was not the die."


def _override_session():
    with Session(engine) as session:
        yield session


app.dependency_overrides[get_session] = _override_session
app.dependency_overrides[require_login] = lambda: None


def _client(monkeypatch=None) -> TestClient:
    if monkeypatch is not None:
        monkeypatch.setattr(discussion_routes, "get_ai_provider", lambda settings: FakeAi())
    return TestClient(app)


def test_every_navigation_page_renders():
    client = _client()
    for path in ("/", "/content", "/content/new", "/discovery", "/discussions", "/discussions/new",
                 "/replies", "/analytics", "/settings"):
        response = client.get(path)
        assert response.status_code == 200, path


def test_favicon_is_served_at_root_and_linked():
    client = _client()
    icon = client.get("/favicon.ico")
    assert icon.status_code == 200
    assert icon.headers["content-type"].startswith("image/")

    svg = client.get("/static/favicon.svg")
    assert svg.status_code == 200
    assert "image/svg" in svg.headers["content-type"]

    page = client.get("/login").text
    assert "/static/favicon.svg" in page
    assert "/static/favicon.ico" in page


def test_manual_post_flows_from_draft_to_published():
    client = _client()
    created = client.post(
        "/content/new",
        data={
            "topic": "Why ground effect came back",
            "body": "Underbody venturi tunnels trade drag for downforce. The cost is sensitivity to ride height.",
            "domain": "mechanical",
            "discipline": "Formula 1",
            "post_format": "short_insight",
        },
        follow_redirects=False,
    )
    assert created.status_code == 303
    item_url = created.headers["location"]
    assert client.get(item_url).status_code == 200

    for action in ("approve", "publish"):
        moved = client.post(f"{item_url}/status", data={"action": action}, follow_redirects=False)
        assert moved.status_code == 303
    assert "Published" in client.get(item_url).text


def test_thread_body_is_split_into_posts():
    client = _client()
    created = client.post(
        "/content/new",
        data={
            "topic": "Chiplet yield",
            "body": "1/ Chiplets trade yield for flexibility.\n---\n2/ A bad die costs less.\n---\n3/ But packaging is the new tax.",
            "domain": "hardware",
            "post_format": "thread",
        },
        follow_redirects=False,
    )
    page = client.get(created.headers["location"]).text
    assert "Thread · 3 posts" in page


def test_saving_a_discussion_and_generating_a_reply(monkeypatch):
    client = _client(monkeypatch)
    created = client.post(
        "/discussions/new",
        data={
            "url": "https://x.com/example/status/1",
            "author": "@engineer",
            "title": "Thermal margins",
            "domain": "hardware",
            "text": "We keep hitting thermal limits at 85C. Is derating the only option?",
        },
        follow_redirects=False,
    )
    assert created.status_code == 303
    url = created.headers["location"]

    drafted = client.post(f"{url}/replies", data={"focus": "add a measurement"}, follow_redirects=False)
    assert drafted.status_code == 303
    page = client.get(url).text
    assert "12% at 85C" in page
    assert "add a concrete measurement" in page


def test_discovery_builds_a_real_search_link():
    client = _client()
    page = client.get("/discovery?terms=chiplets&mode=conversations").text
    assert "x.com/search" in page
    assert "min_faves" in page


def test_generate_creates_a_draft_on_demand(monkeypatch):
    monkeypatch.setattr(content_routes, "get_ai_provider", lambda settings: FakeAi())
    client = _client()
    created = client.post(
        "/content/generate",
        data={"domain": "hardware", "post_format": "short_insight"},
        follow_redirects=False,
    )
    assert created.status_code == 303
    page = client.get(created.headers["location"])
    assert page.status_code == 200
    assert "Draft" in page.text


def test_settings_updates_the_profile():
    client = _client()
    saved = client.post(
        "/settings",
        data={
            "domains": ["hardware", "mechanical"],
            "interests": "chip packaging, aero",
            "style_notes": "short",
            "voice_samples": "",
            "avoid": "no emojis",
            "posts_per_day": "2",
            "include_threads": "on",
        },
        follow_redirects=False,
    )
    assert saved.status_code == 303
    page = client.get("/settings").text
    assert "chip packaging, aero" in page
