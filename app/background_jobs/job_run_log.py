from contextlib import contextmanager
from datetime import date, datetime, timezone
from typing import Iterator, Optional

from sqlmodel import Field, Session, SQLModel, select


class JobRun(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    job_name: str = Field(index=True)
    run_date: date
    status: str = "running"
    items_created: int = 0
    error: Optional[str] = None
    started_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    finished_at: Optional[datetime] = None


def already_completed(session: Session, job_name: str, run_date: date) -> bool:
    query = select(JobRun).where(
        JobRun.job_name == job_name, JobRun.run_date == run_date, JobRun.status == "completed"
    )
    return session.exec(query).first() is not None


@contextmanager
def logged_job_run(session: Session, job_name: str, run_date: date) -> Iterator[JobRun]:
    run = JobRun(job_name=job_name, run_date=run_date)
    session.add(run)
    session.commit()
    try:
        yield run
        run.status = "completed"
    except Exception as error:
        session.rollback()
        run.status = "failed"
        run.error = str(error)[:500]
        raise
    finally:
        run.finished_at = datetime.now(timezone.utc)
        session.add(run)
        session.commit()
