from __future__ import annotations
from dataclasses import dataclass, field
from time import monotonic
from collections import defaultdict
from typing import Dict, Optional

@dataclass
class LoopBudget:
    max_depth: int
    max_requests: int
    max_requests_per_domain: int
    max_new_entities: int
    max_runtime_seconds: int
    request_count: int = 0
    new_entities: int = 0
    domain_requests: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    started: float = field(default_factory=monotonic)
    def can_request(self, depth: int, domain: Optional[str] = None):
        if depth > self.max_depth or self.request_count >= self.max_requests: return False
        if monotonic()-self.started >= self.max_runtime_seconds: return False
        if domain and self.domain_requests[domain] >= self.max_requests_per_domain: return False
        return True
    def record_request(self, domain=None):
        self.request_count+=1
        if domain: self.domain_requests[domain]+=1
    def can_add_entity(self): return self.new_entities < self.max_new_entities
    def record_entity(self): self.new_entities+=1
