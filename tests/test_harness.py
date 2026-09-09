from agent.models.entity import Entity, Provenance
from agent.harness.evaluator import evaluate
from agent.harness.duplicate import compare
from agent.agents.discovery import candidate_from_result, related_results_from_json_ld
from agent.agents.verification import verify_candidate


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

def test_google_places_result_is_authoritatively_verified():
    candidate=candidate_from_result({"name":"Seoul Garden","placeId":"ChIJ123","address":"Tokyo, Japan"}, "Tokyo Korean restaurant")
    result=verify_candidate(candidate, [])
    assert result["official_confirmed"] is True

def test_official_json_ld_brand_becomes_related_candidate():
    parent={"name":"Seoul Garden Tokyo"}
    page={"url":"https://restaurant.example/", "json_ld":[{"@type":"Restaurant","name":"Seoul Garden Tokyo","brand":{"@type":"Brand","name":"Seoul Garden","url":"https://brand.example/"}}]}
    results=related_results_from_json_ld(page, parent)
    assert len(results)==1
    assert results[0]["name"]=="Seoul Garden"
    assert results[0]["sourceUrl"]==page["url"]
    assert results[0]["_relation_type"]=="BRANCH_OF"
