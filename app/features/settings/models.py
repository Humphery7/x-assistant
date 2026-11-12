import json
from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, Session, SQLModel

from app.content.domains import DOMAINS, Domain, all_domains


class Profile(SQLModel, table=True):
    """Single-row owner profile. Personalisation lives here."""

    id: Optional[int] = Field(default=None, primary_key=True)
    disciplines: str = "[]"  # JSON list of domain keys
    interests: str = ""
    style_notes: str = ""
    voice_samples: str = ""
    avoid: str = ""
    posts_per_day: int = 3
    include_threads: bool = True
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    def domain_keys(self) -> list[str]:
        try:
            keys = json.loads(self.disciplines or "[]")
        except (TypeError, ValueError):
            return []
        return [key for key in keys if key in DOMAINS]

    def domains(self) -> list[Domain]:
        keys = self.domain_keys()
        if not keys:
            return all_domains()
        return [DOMAINS[key] for key in keys]

    @property
    def selected_domains(self) -> list[Domain]:
        return self.domains()


def get_profile(session: Session) -> Profile:
    profile = session.get(Profile, 1)
    if profile is None:
        profile = Profile(id=1, disciplines=json.dumps(list(DOMAINS.keys())))
        session.add(profile)
        session.commit()
        session.refresh(profile)
    return profile


def save_profile(
    session: Session,
    *,
    domain_keys: list[str],
    interests: str,
    style_notes: str,
    voice_samples: str,
    avoid: str,
    posts_per_day: int,
    include_threads: bool,
) -> Profile:
    profile = get_profile(session)
    profile.disciplines = json.dumps([key for key in domain_keys if key in DOMAINS])
    profile.interests = interests.strip()
    profile.style_notes = style_notes.strip()
    profile.voice_samples = voice_samples.strip()
    profile.avoid = avoid.strip()
    profile.posts_per_day = max(1, min(6, posts_per_day))
    profile.include_threads = include_threads
    profile.updated_at = datetime.now(timezone.utc)
    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile
