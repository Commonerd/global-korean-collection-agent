from __future__ import annotations
import argparse, logging
from agent.config import Settings
from agent.state.store import StateStore
from agent.adapters.sheets import MockSheetWriter, GoogleSheetsWriter
from agent.adapters.search import MockSearchAdapter, GoogleCSEAdapter
from agent.adapters.places import MockPlacesAdapter, GooglePlacesAdapter
from agent.adapters.web import WebPageAdapter
from agent.adapters.llm import NullLLM, OpenAICompatibleLLM, OllamaLLM
from agent.graph.store import GraphStore
from agent.loop.engine import AutonomousLoop


def build(settings):
    state=StateStore(settings.db_path)
    if settings.mode=="mock":
        sheet=MockSheetWriter(); search=MockSearchAdapter(); places=MockPlacesAdapter()
    else:
        sheet=GoogleSheetsWriter(settings.google_spreadsheet_id,settings.google_sheet_name,settings.google_service_account_json)
        search=GoogleCSEAdapter(settings.google_cse_api_key,settings.google_cse_cx,settings.request_timeout_seconds) if settings.google_cse_api_key and settings.google_cse_cx else MockSearchAdapter()
        places=GooglePlacesAdapter(settings.google_places_api_key,settings.request_timeout_seconds) if settings.enable_places and settings.google_places_api_key else MockPlacesAdapter()
    web=WebPageAdapter(settings.request_timeout_seconds)
    graph=GraphStore(state)
    return state, AutonomousLoop(settings,state,sheet,search,places,web,graph)


def main():
    parser=argparse.ArgumentParser(description="Global Korean Business & Diaspora Autonomous Collection Agent")
    parser.add_argument("--mode",choices=["once","loop","status","review","schema"],default="once")
    parser.add_argument("--iterations",type=int,default=1)
    parser.add_argument("--goal",default=None)
    args=parser.parse_args()
    settings=Settings()
    logging.basicConfig(level=getattr(logging,settings.log_level.upper(),logging.INFO),format="%(asctime)s %(levelname)s %(message)s")
    state, loop=build(settings)
    try:
        if args.mode=="status":
            print(state.counts())
        elif args.mode=="schema":
            print(loop.sheet.read_rows()[:1])
        elif args.mode=="review":
            for row in state.reviews(): print(row)
        elif args.mode=="once":
            print(loop.run(goal=args.goal,iterations=1))
        else:
            print(loop.run(goal=args.goal,iterations=max(1,args.iterations)))
    finally:
        state.close()

if __name__=="__main__": main()
