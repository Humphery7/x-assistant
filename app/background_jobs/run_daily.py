from sqlalchemy.engine import Engine
from sqlmodel import Session

from app.ai.provider import AiProvider, get_ai_provider
from app.background_jobs.daily_content_job import run_daily_content_job
from app.database import create_tables, engine
from app.settings import load_settings


def run_once(ai: AiProvider, database_engine: Engine) -> str:
    """Run the job and return the line to print.

    The result is read while the session is still open. Reading it afterwards
    raises DetachedInstanceError, because committing expires the attributes.
    """
    with Session(database_engine) as session:
        run = run_daily_content_job(session, ai)
        if run is None:
            return "Already done today."
        return f"Created {run.items_created} drafts."


def main() -> None:
    settings = load_settings()
    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY is not set, so no drafts can be generated.")
    create_tables()
    ai = get_ai_provider(settings)
    print(run_once(ai, engine))


if __name__ == "__main__":
    main()
