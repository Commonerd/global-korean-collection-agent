from __future__ import annotations
import requests

class PlacesAdapter:
    def search(self, query: str, context=None) -> list[dict]:
        raise NotImplementedError

class GooglePlacesAdapter(PlacesAdapter):
    URL="https://places.googleapis.com/v1/places:searchText"
    MASK="places.id,places.displayName,places.formattedAddress,places.location,places.websiteUri,places.nationalPhoneNumber"
    def __init__(self, api_key: str, timeout: int=20):
        self.api_key=api_key; self.timeout=timeout
    def search(self, query: str, context=None) -> list[dict]:
        headers={"Content-Type":"application/json","X-Goog-Api-Key":self.api_key,"X-Goog-FieldMask":self.MASK}
        r=requests.post(self.URL, headers=headers, json={"textQuery":query,"pageSize":20}, timeout=self.timeout)
        r.raise_for_status()
        out=[]
        for p in r.json().get("places",[]):
            loc=p.get("location") or {}
            out.append({"name":(p.get("displayName") or {}).get("text"),"address":p.get("formattedAddress"),"website":p.get("websiteUri"),"phone":p.get("nationalPhoneNumber"),"placeId":p.get("id"),"latitude":loc.get("latitude"),"longitude":loc.get("longitude"),"sourceUrl":"https://www.google.com/maps/search/?api=1&query=place_id:"+str(p.get("id")) if p.get("id") else None,"koreanRelevance":query})
        return out

class MockPlacesAdapter(PlacesAdapter):
    def search(self, query: str, context=None) -> list[dict]:
        return []
