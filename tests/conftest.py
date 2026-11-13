import os

# Tests must never read the developer's .env, hit a real database, or call a
# paid API. These are set before any app module is imported.
os.environ["DATABASE_URL"] = "sqlite://"
os.environ["OWNER_PASSWORD"] = "test-password"
os.environ["SESSION_SECRET"] = "test-secret"
os.environ["SECURE_COOKIES"] = "false"
os.environ["GEMINI_API_KEY"] = ""
os.environ.pop("GEMINI_MODEL", None)
