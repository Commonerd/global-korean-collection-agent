from __future__ import annotations
from typing import Any, Literal, Optional
from pydantic import BaseModel, Field

SeedType = Literal["REGION_SEED", "ENTITY_SEED", "RELATION_SEED", "GAP_SEED"]

class Seed(BaseModel):
    seedId: str
    seedType: SeedType
    query: str
    priority: float = 0.0
    depth: int = 0
    context: dict[str, Any] = Field(default_factory=dict)
    status: Literal["PENDING", "RUNNING", "DONE", "FAILED"] = "PENDING"
