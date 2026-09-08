from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


class StateStore:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self._init()

    def _init(self):
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS runs (
            run_id TEXT PRIMARY KEY, current_goal TEXT, depth INTEGER,
            request_count INTEGER, started_at TEXT, updated_at TEXT
        );
        CREATE TABLE IF NOT EXISTS visited_urls (url TEXT PRIMARY KEY, last_seen TEXT);
        CREATE TABLE IF NOT EXISTS visited_queries (query TEXT PRIMARY KEY, last_seen TEXT);
        CREATE TABLE IF NOT EXISTS entities (id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS candidates (candidate_id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS seeds (seed_id TEXT PRIMARY KEY, payload TEXT NOT NULL, updated_at TEXT);
        CREATE TABLE IF NOT EXISTS graph_nodes (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS graph_edges (id TEXT PRIMARY KEY, payload TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS review_queue (id TEXT PRIMARY KEY, kind TEXT, payload TEXT, created_at TEXT);
        """)
        self.db.commit()

    def close(self):
        self.db.close()

    def mark_query(self, query: str) -> bool:
        normalized = " ".join(query.lower().split())
        exists = self.db.execute("SELECT 1 FROM visited_queries WHERE query=?", (normalized,)).fetchone()
        if exists:
            return False
        self.db.execute("INSERT INTO visited_queries(query,last_seen) VALUES(?,?)", (normalized, utcnow()))
        self.db.commit()
        return True

    def mark_url(self, url: str) -> bool:
        exists = self.db.execute("SELECT 1 FROM visited_urls WHERE url=?", (url,)).fetchone()
        if exists:
            return False
        self.db.execute("INSERT INTO visited_urls(url,last_seen) VALUES(?,?)", (url, utcnow()))
        self.db.commit()
        return True

    def save_entity(self, entity):
        payload = entity.model_dump_json()
        self.db.execute("INSERT OR REPLACE INTO entities(id,payload,updated_at) VALUES(?,?,?)", (entity.id, payload, utcnow()))
        self.db.commit()

    def get_entities(self):
        rows = self.db.execute("SELECT payload FROM entities ORDER BY updated_at").fetchall()
        return [json.loads(r[0]) for r in rows]

    def save_candidate(self, candidate):
        self.db.execute("INSERT OR REPLACE INTO candidates(candidate_id,payload,updated_at) VALUES(?,?,?)", (candidate.candidateId, candidate.model_dump_json(), utcnow()))
        self.db.commit()

    def add_review(self, item_id: str, kind: str, payload: dict):
        self.db.execute("INSERT OR REPLACE INTO review_queue(id,kind,payload,created_at) VALUES(?,?,?,?)", (item_id, kind, json.dumps(payload, ensure_ascii=False), utcnow()))
        self.db.commit()

    def reviews(self):
        return [dict(r) for r in self.db.execute("SELECT * FROM review_queue ORDER BY created_at DESC").fetchall()]

    def save_seed(self, seed):
        self.db.execute("INSERT OR REPLACE INTO seeds(seed_id,payload,updated_at) VALUES(?,?,?)", (seed.seedId, seed.model_dump_json(), utcnow()))
        self.db.commit()

    def pending_seeds(self):
        from agent.models.seed import Seed
        rows = self.db.execute("SELECT payload FROM seeds WHERE json_extract(payload,'$.status')='PENDING' ORDER BY updated_at DESC").fetchall()
        return [Seed.model_validate_json(r[0]) for r in rows]

    def add_graph_node(self, node):
        self.db.execute("INSERT OR REPLACE INTO graph_nodes(id,payload) VALUES(?,?)", (node.id, node.model_dump_json()))
        self.db.commit()

    def add_graph_edge(self, edge):
        self.db.execute("INSERT OR REPLACE INTO graph_edges(id,payload) VALUES(?,?)", (edge.id, edge.model_dump_json()))
        self.db.commit()

    def counts(self):
        out = {}
        for table in ["entities","candidates","visited_urls","visited_queries","seeds","graph_nodes","graph_edges","review_queue"]:
            out[table] = self.db.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
        return out
