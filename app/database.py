from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from app.settings import load_settings


def normalise_database_url(url: str) -> str:
    for prefix in ("postgres://", "postgresql://"):
        if url.startswith(prefix):
            return "postgresql+psycopg://" + url[len(prefix):]
    return url


def make_engine(url: str):
    url = normalise_database_url(url)
    if url.startswith("sqlite"):
        Path("data").mkdir(exist_ok=True)
        return create_engine(url, connect_args={"check_same_thread": False})
    return create_engine(url, pool_pre_ping=True)


engine = make_engine(load_settings().database_url)


def create_tables() -> None:
    from app.background_jobs import job_run_log  # noqa: F401
    from app.features.content_studio import models as content_models  # noqa: F401
    from app.features.discussions import models as discussion_models  # noqa: F401
    from app.features.discovery import models as discovery_models  # noqa: F401
    from app.features.settings import models as settings_models  # noqa: F401

    SQLModel.metadata.create_all(engine)


def get_session():
    with Session(engine) as session:
        yield session
