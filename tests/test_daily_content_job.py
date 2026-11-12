from datetime import date

import pytest
from sqlmodel import Session, SQLModel, create_engine, select
from sqlmodel.pool import StaticPool

from app.background_jobs.daily_content_job import POSTS_PER_DAY, run_daily_content_job
from app.background_jobs.job_run_log import JobRun
from app.features.content_studio.models import ContentItem, ContentStatus

TODAY = date(2026, 11, 12)


class FakeAi:
    def generate_text(self, prompt: str) -> str:
        return "  Retries without jitter cause thundering herds.  "


class BrokenAi:
    def generate_text(self, prompt: str) -> str:
        raise RuntimeError("quota exceeded")


@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as db_session:
        yield db_session


def test_job_creates_drafts_and_logs_a_completed_run(session):
    run = run_daily_content_job(session, FakeAi(), TODAY)
    drafts = session.exec(select(ContentItem)).all()
    assert run.status == "completed" and run.items_created == POSTS_PER_DAY
    assert len(drafts) == POSTS_PER_DAY
    assert all(d.status == ContentStatus.DRAFT and d.scheduled_for == TODAY for d in drafts)
    assert drafts[0].body == "Retries without jitter cause thundering herds."


def test_job_does_not_run_twice_on_the_same_day(session):
    run_daily_content_job(session, FakeAi(), TODAY)
    assert run_daily_content_job(session, FakeAi(), TODAY) is None
    assert len(session.exec(select(ContentItem)).all()) == POSTS_PER_DAY


def test_failed_job_is_logged_and_leaves_no_partial_drafts(session):
    with pytest.raises(RuntimeError):
        run_daily_content_job(session, BrokenAi(), TODAY)
    run = session.exec(select(JobRun)).one()
    assert run.status == "failed" and "quota" in run.error
    assert session.exec(select(ContentItem)).all() == []
    assert run_daily_content_job(session, FakeAi(), TODAY).status == "completed"
