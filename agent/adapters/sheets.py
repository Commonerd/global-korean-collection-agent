from __future__ import annotations
import json
from pathlib import Path

class SheetWriter:
    def read_rows(self) -> list[dict]: raise NotImplementedError
    def append_entity(self, entity): raise NotImplementedError
    def update_entity(self, entity): raise NotImplementedError
    def find_existing(self, key: str): raise NotImplementedError

class MockSheetWriter(SheetWriter):
    def __init__(self):
        self.rows=[]
    def read_rows(self): return list(self.rows)
    def append_entity(self, entity): self.rows.append(entity.model_dump(mode="json"))
    def update_entity(self, entity):
        for i,row in enumerate(self.rows):
            if row.get("id")==entity.id: self.rows[i]=entity.model_dump(mode="json")
    def find_existing(self,key): return next((x for x in self.rows if x.get("id")==key), None)

class GoogleSheetsWriter(SheetWriter):
    def __init__(self, spreadsheet_id: str, sheet_name: str, service_account_json: str=""):
        from googleapiclient.discovery import build
        from google.oauth2.service_account import Credentials
        scopes=["https://www.googleapis.com/auth/spreadsheets"]
        if service_account_json:
            creds=Credentials.from_service_account_file(service_account_json, scopes=scopes)
        else:
            import google.auth
            creds,_=google.auth.default(scopes=scopes)
        self.service=build("sheets","v4",credentials=creds,cache_discovery=False)
        self.spreadsheet_id=spreadsheet_id
        self.sheet_name=sheet_name
    def read_rows(self):
        result=self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=f"{self.sheet_name}!A:Z").execute()
        values=result.get("values",[])
        if not values: return []
        headers=values[0]
        return [dict(zip(headers,row)) for row in values[1:]]
    def _headers(self):
        result=self.service.spreadsheets().values().get(spreadsheetId=self.spreadsheet_id, range=f"{self.sheet_name}!1:1").execute()
        return result.get("values", [[]])[0]
    def append_entity(self, entity):
        headers=self._headers(); payload=entity.model_dump(mode="json")
        alias_map={
            "id":["id","ID","entity_id"],
            "name":["name","Name","상호","기관명","장소명"],
            "nameKo":["nameKo","name_ko","한국어명","한글명"],
            "nameEn":["nameEn","name_en","영문명"],
            "entityType":["entityType","type","유형"],
            "category":["category","카테고리"],
            "country":["country","국가"],
            "city":["city","도시"],
            "address":["address","주소"],
            "latitude":["latitude","lat","위도"],
            "longitude":["longitude","lng","lon","경도"],
            "website":["website","url","웹사이트","홈페이지"],
            "phone":["phone","전화","전화번호"],
            "placeId":["placeId","place_id","Google Place ID"],
            "koreanRelevance":["koreanRelevance","korean_relevance","한국관련성"],
            "parentEntityId":["parentEntityId","parent_id","상위ID"],
            "verificationStatus":["verificationStatus","verification_status","검증상태"],
            "confidenceScore":["confidenceScore","confidence","신뢰도"],
            "provenance":["provenance","sources","출처"],
            "discoveredAt":["discoveredAt","수집일"],
            "updatedAt":["updatedAt","수정일"]
        }
        canonical_for_header={}
        for field, aliases in alias_map.items():
            for alias in aliases:
                if alias in headers:
                    canonical_for_header[alias]=field
                    break
        row=[]
        for h in headers:
            field=canonical_for_header.get(h,h)
            v=payload.get(field,"")
            row.append(json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v)
        body={"values":[row]}
        return self.service.spreadsheets().values().append(spreadsheetId=self.spreadsheet_id, range=f"{self.sheet_name}!A:Z", valueInputOption="RAW", insertDataOption="INSERT_ROWS", body=body).execute()
    def update_entity(self, entity):
        # Safe default: do not overwrite unknown rows automatically.
        raise NotImplementedError("update_entity intentionally disabled; implement row-keyed update after schema confirmation")
    def find_existing(self,key):
        for row in self.read_rows():
            if str(row.get("id", ""))==str(key): return row
        return None
