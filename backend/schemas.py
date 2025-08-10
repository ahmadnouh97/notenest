from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, HttpUrl, field_validator


class NoteCreate(BaseModel):
    url: HttpUrl
    title: Optional[str] = None
    description: Optional[str] = None
    tags: List[str] = []

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: List[str]) -> List[str]:
        return [t.strip() for t in v if t.strip()]


class NoteUpdate(BaseModel):
    url: Optional[HttpUrl] = None
    title: Optional[str] = None
    description: Optional[str] = None
    tags: Optional[List[str]] = None


class NoteOut(BaseModel):
    id: str
    url: str
    title: str
    description: str
    tags: List[str]
    created_at: str
    updated_at: str


