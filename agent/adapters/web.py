from __future__ import annotations
from urllib.parse import urlparse
import time, requests
from bs4 import BeautifulSoup
import json

class WebPageAdapter:
    def __init__(self, timeout=20, max_chars=8000):
        self.timeout=timeout; self.max_chars=max_chars
    def fetch(self, url: str) -> dict:
        host=urlparse(url).netloc.lower()
        headers={"User-Agent":"GlobalKoreanCollectionAgent/0.1 (+research bot)"}
        r=requests.get(url, headers=headers, timeout=self.timeout)
        r.raise_for_status()
        soup=BeautifulSoup(r.text,"html.parser")
        json_ld=[]
        for script in soup.find_all("script", attrs={"type":"application/ld+json"}):
            try:
                json_ld.append(json.loads(script.string or script.get_text()))
            except (TypeError, json.JSONDecodeError):
                continue
        for tag in soup(["script","style","noscript"]): tag.decompose()
        text=" ".join(soup.stripped_strings)
        return {"url":url,"title":soup.title.get_text(" ",strip=True) if soup.title else host,"text":text[:self.max_chars],"json_ld":json_ld,"status_code":r.status_code}
