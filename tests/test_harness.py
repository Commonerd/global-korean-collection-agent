from agent.models.entity import Entity, Provenance
from agent.harness.evaluator import evaluate
from agent.harness.duplicate import compare


def entity():
    return Entity(id="1",name="Test",entityType="BUSINESS",country="Japan",city="Tokyo",address="Tokyo Japan",website="https://example.com",provenance=[Provenance(sourceName="Official",sourceUrl="https://example.com",sourceType="official")])

def test_harness_confirms_strong_entity():
    e=entity()
    r=evaluate(e,independent_sources=1,official_confirmed=True,location_confirmed=True,relevance_clear=True)
    assert r.status=="CONFIRMED"
    assert r.score==80

def test_duplicate_place_id():
    e=entity(); e.placeId="abc"
    status,_=compare(e,[{"id":"old","name":"Other","placeId":"abc"}])
    assert status=="EXISTING"
