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


class SearchRequest(BaseModel):
    query: str
    tags: Optional[List[str]] = None
    topK: Optional[int] = 10
    hybridWeight: Optional[float] = 0.7

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        return [t.strip() for t in v if t and t.strip()]


class SearchResultItem(BaseModel):
    note: NoteOut
    score: float


class ChatMessageIn(BaseModel):
    role: str
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessageIn]
    topK: Optional[int] = 5
    tags: Optional[List[str]] = None
    provider: Optional[str] = "mock"
    model: Optional[str] = "dummy"
    apiKey: Optional[str] = None

    @field_validator("tags")
    @classmethod
    def normalize_tags(cls, v: Optional[List[str]]) -> Optional[List[str]]:
        if v is None:
            return None
        return [t.strip() for t in v if t and t.strip()]

