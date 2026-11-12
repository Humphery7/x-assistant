# X Assistant

A personal dashboard that prepares engineering content and engagement for you to
review and publish by hand on X.

It never publishes, likes or replies for you, and it does not use the X API.
Discussion discovery works by building X advanced-search links you open
yourself; you paste the conversation back in when you want a reply drafted.

## What it does

- **Content Studio** — drafts across software, hardware, robotics, mechanical,
  aerospace, civil and biomedical engineering. Edit, approve, reject, copy and
  mark published. Threads are split into individual posts with character counts.
- **Discussion Discovery** — one-click X advanced searches per field and per
  recent topic, plus saved searches. No key, no quota.
- **Saved Discussions / Engagement Assistant** — paste a post or thread, get a
  reply that adds something, rewrite it with a note, then approve it.
- **Personalisation** — pick your fields, interests, style notes, your own
  writing samples and things to avoid. All of it is injected into the prompts.
- **Daily job** — proposes fresh topics, then writes 1–6 drafts per day using
  your profile. Runs from GitHub Actions, logs every run, and is idempotent.
- **Analytics** — posts by field and format, review funnel, replies and job runs.

## Run locally

    pip install -r requirements.txt
    cp .env.example .env        # set OWNER_PASSWORD and SESSION_SECRET
    uvicorn app.main:app --reload
    python -m app.background_jobs.run_daily   # generate today's drafts (needs GEMINI_API_KEY)
    pytest

Then open http://127.0.0.1:8000, sign in, and fill in Settings. The profile is
what stops the drafts reading like generic AI output.

## Free deployment

1. Neon: create a free Postgres project, copy its connection string.
2. GitHub: push this repo, add secrets `DATABASE_URL` and `GEMINI_API_KEY`. The
   `daily-jobs` workflow runs the job daily (also runnable from the Actions tab).
3. Render free web service: build `pip install -r requirements.txt`, start
   `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Set `DATABASE_URL`,
   `OWNER_PASSWORD`, `SESSION_SECRET`, `SECURE_COOKIES=true`.

## Layout

- `app/content/`: engineering domains and topic banks, the day planner, X search
  link builder
- `app/features/<name>/`: one folder per navigation item (routes and models)
- `app/background_jobs/`: scheduled jobs and the job run log
- `app/ai/`: AI provider interface, Gemini implementation, prompts
- `app/web/`: shared templates and CSS
