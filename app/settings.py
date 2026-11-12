import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    database_url: str
    owner_password: str
    session_secret: str
    secure_cookies: bool
    gemini_api_key: str
    gemini_model: str


def load_settings() -> Settings:
    return Settings(
        database_url=os.getenv("DATABASE_URL", "sqlite:///data/assistant.db"),
        owner_password=os.getenv("OWNER_PASSWORD", ""),
        session_secret=os.getenv("SESSION_SECRET", ""),
        secure_cookies=os.getenv("SECURE_COOKIES", "false").lower() == "true",
        gemini_api_key=os.getenv("GEMINI_API_KEY", ""),
        gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
    )
