from datetime import datetime

from pydantic import BaseModel, HttpUrl


class FeedOut(BaseModel):
    id: int
    name: str
    url: str
    category: str
    language: str
    is_active: bool
    last_fetched_at: datetime | None = None
    last_fetched_status: str | None = None
    last_error: str | None = None
    fetch_interval_minutes: int

    model_config = {"from_attributes": True}


class FeedCreate(BaseModel):
    name: str
    url: HttpUrl
    category: str
    language: str = "ko"


class FeedPatch(BaseModel):
    is_active: bool | None = None

