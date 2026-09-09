from __future__ import annotations
import requests

class SearchAdapter:
    def search(self, query: str, context=None) -> list[dict]:
        raise NotImplementedError

class GoogleCSEAdapter(SearchAdapter):
    def __init__(self, api_key: str, cx: str, timeout: int = 20):
        self.api_key=api_key; self.cx=cx; self.timeout=timeout
    def search(self, query: str, context=None) -> list[dict]:
        r=requests.get("https://www.googleapis.com/customsearch/v1", params={"key":self.api_key,"cx":self.cx,"q":query}, timeout=self.timeout)
        r.raise_for_status()
        data=r.json()
        return [{"name":i.get("title"),"sourceUrl":i.get("link"),"snippet":i.get("snippet"),"website":i.get("link")} for i in data.get("items",[])]

class MockSearchAdapter(SearchAdapter):
    DATA = [
        {"name":"Seoul Garden Tokyo","address":"Tokyo, Japan","website":"https://example.com/seoul-garden-tokyo","sourceUrl":"https://example.com/seoul-garden-tokyo","koreanRelevance":"Korean restaurant"},
        {"name":"Korea Mart Osaka","address":"Osaka, Japan","website":"https://example.com/korea-mart-osaka","sourceUrl":"https://example.com/korea-mart-osaka","koreanRelevance":"Korean grocery market"},
        {"name":"Korean Business Association Tokyo","address":"Tokyo, Japan","website":"https://example.com/kbat","sourceUrl":"https://example.com/kbat","koreanRelevance":"Korean community organization"},
    ]
    def search(self, query: str, context=None) -> list[dict]:
        q=query.lower()
        return [x for x in self.DATA if any(token in (x["name"]+" "+x.get("koreanRelevance","")).lower() for token in q.split() if len(token)>2)] or self.DATA[:2]


class EmptySearchAdapter(SearchAdapter):
    def search(self, query: str, context=None) -> list[dict]:
        return []
