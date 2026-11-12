from datetime import datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class DiscussionStatus:
    SAVED = "saved"
    REPLIED = "replied"
    ARCHIVED = "archived"


class ReplyStatus:
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"


class Discussion(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    url: str = ""
    author: str = ""
    title: str = ""
    domain: str = Field(default="software", index=True)
    text: str = ""
    notes: str = ""
    status: str = Field(default=DiscussionStatus.SAVED, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class Reply(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    discussion_id: int = Field(index=True, foreign_key="discussion.id")
    body: str
    approach: str = ""
    status: str = Field(default=ReplyStatus.DRAFT, index=True)
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
