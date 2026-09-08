from __future__ import annotations
from pydantic import BaseModel
from typing import Literal

NodeType = Literal["KOREATOWN","BUSINESS","COMPANY","BRANCH","ORGANIZATION","PERSON_PUBLIC","BRAND","CITY","COUNTRY","SOURCE"]

class GraphNode(BaseModel):
    id: str
    nodeType: str
    label: str
    attributes: dict = {}

class GraphEdge(BaseModel):
    id: str
    sourceId: str
    targetId: str
    relation: str
    attributes: dict = {}
