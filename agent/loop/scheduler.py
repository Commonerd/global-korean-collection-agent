from __future__ import annotations
import heapq

class SeedQueue:
    def __init__(self): self.heap=[]; self.counter=0
    def push(self, seed):
        self.counter+=1; heapq.heappush(self.heap, (-seed.priority,self.counter,seed))
    def pop(self): return heapq.heappop(self.heap)[2] if self.heap else None
    def __len__(self): return len(self.heap)
