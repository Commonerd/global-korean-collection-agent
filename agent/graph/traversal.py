from __future__ import annotations
import sqlite3

def neighbors(state, node_id: str):
    rows=state.db.execute("SELECT payload FROM graph_edges").fetchall()
    out=[]
    import json
    for r in rows:
        e=json.loads(r[0])
        if e["sourceId"]==node_id: out.append(e["targetId"])
        if e["targetId"]==node_id: out.append(e["sourceId"])
    return out
