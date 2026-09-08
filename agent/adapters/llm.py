from __future__ import annotations
import requests

class LLMProvider:
    def generate(self, prompt: str) -> str:
        raise NotImplementedError

class NullLLM(LLMProvider):
    def generate(self, prompt: str) -> str:
        return ""

class OpenAICompatibleLLM(LLMProvider):
    def __init__(self, base_url, api_key, model, timeout=60):
        self.base_url=base_url.rstrip("/"); self.api_key=api_key; self.model=model; self.timeout=timeout
    def generate(self, prompt: str) -> str:
        r=requests.post(self.base_url+"/chat/completions", headers={"Authorization":f"Bearer {self.api_key}","Content-Type":"application/json"}, json={"model":self.model,"messages":[{"role":"user","content":prompt}],"temperature":0}, timeout=self.timeout)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]

class OllamaLLM(LLMProvider):
    def __init__(self, base_url, model, timeout=120): self.base_url=base_url.rstrip("/"); self.model=model; self.timeout=timeout
    def generate(self, prompt: str) -> str:
        r=requests.post(self.base_url+"/api/generate", json={"model":self.model,"prompt":prompt,"stream":False}, timeout=self.timeout)
        r.raise_for_status(); return r.json().get("response","")
