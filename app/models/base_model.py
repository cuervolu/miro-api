from datetime import datetime, timezone
from typing import Optional

from pydantic import BaseModel, Field


class BaseCreateModel(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = 'draft'


class BaseUpdateModel(BaseModel):
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: Optional[str]


class BaseReadModel(BaseModel):
    id: str
    created_at: datetime
    updated_at: datetime
    status: str

