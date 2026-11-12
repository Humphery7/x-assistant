from datetime import date, datetime, timezone
from typing import Optional

from sqlmodel import Field, SQLModel


class ContentStatus:
    IDEA = "idea"
    DRAFT = "draft"
    APPROVED = "approved"
    PUBLISHED = "published"
    REJECTED = "rejected"


STATUS_LABELS = {
    ContentStatus.IDEA: "Idea",
    ContentStatus.DRAFT: "Draft",
    ContentStatus.APPROVED: "Approved",
    ContentStatus.PUBLISHED: "Published",
    ContentStatus.REJECTED: "Rejected",
}

# The review flow the dashboard exposes.
NEXT_STATUS = {
    ContentStatus.IDEA: ContentStatus.DRAFT,
    ContentStatus.DRAFT: ContentStatus.APPROVED,
    ContentStatus.APPROVED: ContentStatus.PUBLISHED,
}


class ContentSource:
    DAILY_JOB = "daily_job"
    MANUAL = "manual"
    ON_DEMAND = "on_demand"


class ContentItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    domain: str = Field(default="software", index=True)
    discipline: str = ""
    topic: str
    post_format: str
    body: str
    angle: str = ""
    rationale: str = ""
    status: str = Field(default=ContentStatus.DRAFT, index=True)
    source: str = ContentSource.MANUAL
    scheduled_for: Optional[date] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    published_at: Optional[datetime] = None


class ThreadPost(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    content_item_id: int = Field(index=True, foreign_key="contentitem.id")
    position: int = 0
    body: str = ""
