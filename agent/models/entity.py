from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field, field_validator

VerificationStatus = Literal["CONFIRMED", "NEEDS_REVIEW", "UNVERIFIED", "REJECTED"]


class Provenance(BaseModel):
    sourceName: str
    sourceUrl: Optional[str] = None
    sourceType: str
    collectedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    verificationMethod: Optional[str] = None
    evidence: Optional[str] = None


class Entity(BaseModel):
    id: str
    name: str
    nameKo: Optional[str] = None
    nameEn: Optional[str] = None
    entityType: str
    category: Optional[str] = None
    country: Optional[str] = None
    city: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    website: Optional[str] = None
    phone: Optional[str] = None
    placeId: Optional[str] = None
    koreanRelevance: Optional[str] = None
    parentEntityId: Optional[str] = None
    verificationStatus: VerificationStatus = "UNVERIFIED"
    confidenceScore: int = Field(default=0, ge=0, le=100)
    provenance: list[Provenance]
    discoveredAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updatedAt: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("name")
    @classmethod
    def name_required(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("name must not be empty")
        return value

    @field_validator("latitude")
    @classmethod
    def latitude_range(cls, value):
        if value is not None and not -90 <= value <= 90:
            raise ValueError("latitude out of range")
        return value

    @field_validator("longitude")
    @classmethod
    def longitude_range(cls, value):
        if value is not None and not -180 <= value <= 180:
            raise ValueError("longitude out of range")
        return value
