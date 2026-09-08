from agent.config import Settings
from agent.state.store import StateStore
from agent.adapters.sheets import MockSheetWriter
from agent.adapters.search import MockSearchAdapter
from agent.adapters.places import MockPlacesAdapter
from agent.adapters.web import WebPageAdapter
from agent.graph.store import GraphStore
from agent.loop.engine import AutonomousLoop
from pathlib import Path

def test_mock_end_to_end(tmp_path):
    s=Settings(database_path=str(tmp_path/'a.db'),review_queue_path=str(tmp_path/'review.jsonl'),mode='mock',dry_run=False,max_requests_per_run=20,max_new_entities_per_run=3)
    state=StateStore(Path(s.database_path)); sheet=MockSheetWriter()
    loop=AutonomousLoop(s,state,sheet,MockSearchAdapter(),MockPlacesAdapter(),WebPageAdapter(),GraphStore(state))
    result=loop.run(goal='Tokyo Korean restaurant',iterations=1)
    assert result['counts']['candidates']>0
    assert result['counts']['entities']>0
    assert len(sheet.rows)>0
    state.close()
