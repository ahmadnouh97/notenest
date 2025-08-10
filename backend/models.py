from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass(slots=True)
class Note:
    id: str
    url: str
    title: str
    description: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime
    embedding: Optional[list[float]] = None


