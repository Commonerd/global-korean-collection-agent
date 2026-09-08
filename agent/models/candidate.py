from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field


class Candidate(BaseModel):
    candidateId: str
    rawName: Optional[str] = None
    rawAddress: Optional[str] = None
    discoveredFrom: str
    sourceUrls: list[str] = Field(default_factory=list)
    extractedData: dict[str, Any] = Field(default_factory=dict)
    relatedEntityIds: list[str] = Field(default_factory=list)
    status: Literal["NEW", "INVESTIGATING", "ACCEPTED", "REJECTED"] = "NEW"
