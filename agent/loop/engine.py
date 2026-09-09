from __future__ import annotations
import json, logging, hashlib
from typing import Optional
from urllib.parse import urlparse
from datetime import datetime, timezone
from agent.agents.discovery import candidate_from_result
from agent.agents.resolution import resolve
from agent.agents.verification import verify_candidate
from agent.harness.evaluator import evaluate
from agent.models.entity import Entity
from agent.models.seed import Seed
from agent.loop.scheduler import SeedQueue
from agent.loop.policy import LoopBudget

log=logging.getLogger(__name__)

class AutonomousLoop:
    def __init__(self, settings, state, sheet, search, places, web, graph):
        self.settings=settings; self.state=state; self.sheet=sheet; self.search=search; self.places=places; self.web=web; self.graph=graph

    def run(self, goal: Optional[str] = None, iterations: int = 1):
        existing=self.sheet.read_rows()
        for i in range(iterations):
            budget=LoopBudget(self.settings.max_depth,self.settings.max_requests_per_run,self.settings.max_requests_per_domain,self.settings.max_new_entities_per_run,self.settings.max_runtime_seconds)
            seeds=[]
            if goal: seeds.append(Seed(seedId=hashlib.sha1(goal.encode()).hexdigest()[:16],seedType="REGION_SEED",query=goal,priority=100,depth=0))
            from agent.agents.planner import coverage_seeds
            for seed in coverage_seeds(existing)[:10]: seeds.append(seed)
            q=SeedQueue()
            for s in seeds:
                self.state.save_seed(s)
                q.push(s)
            self._iteration(q,budget,existing,goal_query=goal)
            existing=self.sheet.read_rows()
        return {"counts": self.state.counts()}

    def _iteration(self,q,budget,existing,goal_query=None):
        while len(q) and budget.can_add_entity():
            seed=q.pop()
            if seed.depth>self.settings.max_depth: continue
            if seed.query != goal_query and not self.state.mark_query(seed.query): continue
            log.info("SEARCH %s", seed.query)
            results=[]
            if self.settings.mode=="mock":
                results=self.search.search(seed.query,{})
            else:
                if not budget.can_request(seed.depth): break
                budget.record_request()
                results=self.search.search(seed.query,{})
                if self.settings.enable_web_search and self.settings.google_cse_api_key:
                    pass
                if self.settings.enable_places and self.settings.google_places_api_key:
                    results += self.places.search(seed.query,{})
            for result in results:
                if not budget.can_add_entity(): break
                cand=candidate_from_result(result, seed.query)
                self.state.save_candidate(cand)
                fetched=[]
                for url in cand.sourceUrls[:3]:
                    domain=urlparse(url).netloc.lower()
                    if not url or not budget.can_request(seed.depth, domain): continue
                    if not self.state.mark_url(url): continue
                    if self.settings.mode=="mock":
                        fetched.append({"url":url,"title":cand.rawName or "Mock source","text":"Official-looking mock evidence"})
                    else:
                        try:
                            budget.record_request(domain)
                            fetched.append(self.web.fetch(url))
                        except Exception as exc:
                            log.warning("fetch failed %s: %s", url, exc)
                ver=verify_candidate(cand,fetched)
                if self.settings.mode == "mock":
                    ver["official_confirmed"] = True
                    ver["independent_sources"] = max(ver["independent_sources"], 1)
                data=cand.extractedData.copy()
                entity_id=hashlib.sha1(f"{data.get('name')}|{data.get('address')}|{data.get('website')}".encode()).hexdigest()[:16]
                entity=Entity(id=entity_id,name=data.get("name") or cand.rawName or "Unknown",entityType=self._entity_type(data),category=self._category(data),country=data.get("country") or self._guess_country(data.get("address")),city=data.get("city") or self._guess_city(data.get("address")),address=data.get("address"),latitude=data.get("latitude"),longitude=data.get("longitude"),website=data.get("website"),phone=data.get("phone"),placeId=data.get("placeId"),koreanRelevance=data.get("koreanRelevance"),provenance=ver["provenance"] or [{"sourceName":"query","sourceType":"search","verificationMethod":"query","evidence":seed.query}],verificationStatus="UNVERIFIED")
                dup,_=resolve(entity,existing)
                hr=evaluate(entity,dup,**{k:ver[k] for k in ["independent_sources","official_confirmed","location_confirmed","relevance_clear"]})
                entity.confidenceScore=hr.score; entity.verificationStatus=hr.status; entity.updatedAt=datetime.now(timezone.utc).isoformat()
                self.graph.add_entity(entity)
                self.state.save_entity(entity)
                if hr.status=="CONFIRMED" and dup=="NEW":
                    if self.settings.dry_run:
                        log.info("WRITE skipped for %s: DRY_RUN=true", entity.id)
                    else:
                        log.info("WRITE %s: status=%s duplicate=%s score=%s", entity.id, hr.status, dup, hr.score)
                        self.sheet.append_entity(entity)
                    budget.record_entity()
                    # Relation/Entity seed from the newly approved entity.
                    if seed.depth+1 <= self.settings.max_depth:
                        rel=f"{entity.name} overseas branches"
                        next_seed=Seed(seedId=hashlib.sha1(rel.encode()).hexdigest()[:16],seedType="RELATION_SEED",query=rel,priority=max(seed.priority-10,1),depth=seed.depth+1,context={"entityId":entity.id})
                        self.state.save_seed(next_seed)
                        q.push(next_seed)
                else:
                    self.state.add_review(entity.id, "HARNESS", {"entity":entity.model_dump(mode="json"),"errors":hr.errors,"duplicate":dup})
                    budget.record_entity()

    @staticmethod
    def _entity_type(data):
        text=(data.get("koreanRelevance") or data.get("name") or "").lower()
        if "association" in text or "organization" in text: return "ORGANIZATION"
        if "company" in text or "office" in text: return "COMPANY"
        if "brand" in text: return "BRAND"
        return "BUSINESS"
    @staticmethod
    def _category(data):
        text=(data.get("koreanRelevance") or data.get("name") or "").lower()
        for x in ["restaurant","market","service","office","organization","corporate"]:
            if x in text: return x
        return "other"
    @staticmethod
    def _guess_country(address):
        if not address: return None
        a=address.lower()
        if "japan" in a or "tokyo" in a or "osaka" in a: return "Japan"
        if "korea" in a or "seoul" in a: return "South Korea"
        return None
    @staticmethod
    def _guess_city(address):
        if not address: return None
        for city in ["Tokyo","Osaka","Seoul","Los Angeles","New York","Toronto","Sydney"]:
            if city.lower() in address.lower(): return city
        return None
