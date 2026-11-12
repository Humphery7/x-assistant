from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class SavedSearch(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    label: str
    query: str
    domain: str = ""
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
