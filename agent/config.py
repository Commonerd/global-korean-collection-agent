from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


def _bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "y", "on"}


@dataclass
class Settings:
    mode: str = os.getenv("MODE", "mock")
    dry_run: bool = _bool("DRY_RUN", True)
    database_path: str = os.getenv("DATABASE_PATH", "data/agent.db")
    review_queue_path: str = os.getenv("REVIEW_QUEUE_PATH", "data/review_queue.jsonl")
    log_dir: str = os.getenv("LOG_DIR", "data/logs")
    log_file: str = os.getenv("LOG_FILE", "agent.log")
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    max_depth: int = int(os.getenv("MAX_DEPTH", "3"))
    max_requests_per_run: int = int(os.getenv("MAX_REQUESTS_PER_RUN", "30"))
    max_requests_per_domain: int = int(os.getenv("MAX_REQUESTS_PER_DOMAIN", "8"))
    max_new_entities_per_run: int = int(os.getenv("MAX_NEW_ENTITIES_PER_RUN", "10"))
    max_runtime_seconds: int = int(os.getenv("MAX_RUNTIME_SECONDS", "300"))
    max_retries: int = int(os.getenv("MAX_RETRIES", "2"))
    request_timeout_seconds: int = int(os.getenv("REQUEST_TIMEOUT_SECONDS", "20"))

    google_spreadsheet_id: str = os.getenv("GOOGLE_SPREADSHEET_ID", "")
    google_sheet_name: str = os.getenv("GOOGLE_SHEET_NAME", "Sheet1")
    google_service_account_json: str = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON", "")

    enable_web_search: bool = _bool("ENABLE_WEB_SEARCH", True)
    google_cse_api_key: str = os.getenv("GOOGLE_CSE_API_KEY", "")
    google_cse_cx: str = os.getenv("GOOGLE_CSE_CX", "")
    enable_places: bool = _bool("ENABLE_PLACES", False)
    google_places_api_key: str = os.getenv("GOOGLE_PLACES_API_KEY", "")

    llm_provider: str = os.getenv("LLM_PROVIDER", "none")
    llm_base_url: str = os.getenv("LLM_BASE_URL", "")
    llm_api_key: str = os.getenv("LLM_API_KEY", "")
    llm_model: str = os.getenv("LLM_MODEL", "")

    @property
    def db_path(self) -> Path:
        path = Path(self.database_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def review_path(self) -> Path:
        path = Path(self.review_queue_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return path

    @property
    def log_path(self) -> Path:
        path = Path(self.log_dir) / self.log_file
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
