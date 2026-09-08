from agent.graph.model import GraphNode, GraphEdge
from agent.state.store import StateStore

class GraphStore:
    def __init__(self, state: StateStore): self.state=state
    def add_entity(self, entity):
        node_type = entity.entityType if entity.entityType else "BUSINESS"
        self.state.add_graph_node(GraphNode(id=entity.id,nodeType=node_type,label=entity.name,attributes=entity.model_dump(mode="json")))
        if entity.parentEntityId:
            self.add_edge(entity.id, entity.parentEntityId, "BELONGS_TO")
        if entity.city:
            self.add_edge(entity.id, "city:"+entity.city.lower().replace(" ","_"), "LOCATED_IN")
    def add_edge(self, source, target, relation):
        eid=f"{source}|{relation}|{target}"
        self.state.add_graph_edge(GraphEdge(id=eid,sourceId=source,targetId=target,relation=relation))
