from sqlmodel import Session

from app.ai.provider import get_ai_provider
from app.background_jobs.daily_content_job import run_daily_content_job
from app.database import create_tables, engine
from app.settings import load_settings


def main() -> None:
    settings = load_settings()
    if not settings.gemini_api_key:
        raise SystemExit("GEMINI_API_KEY is not set, so no drafts can be generated.")
    create_tables()
    ai = get_ai_provider(settings)
    with Session(engine) as session:
        run = run_daily_content_job(session, ai)
    print("Already done today." if run is None else f"Created {run.items_created} drafts.")


if __name__ == "__main__":
    main()
