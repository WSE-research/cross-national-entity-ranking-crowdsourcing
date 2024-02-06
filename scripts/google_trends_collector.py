from pytrends.request import TrendReq
from SPARQLWrapper import SPARQLWrapper, JSON

sparql = SPARQLWrapper("https://query.wikidata.org/sparql")
sparql_dbpedia = SPARQLWrapper("https://dbpedia.org/sparql")


def get_freebase_id_of_dbpedia_class(dbpedia_class: str):

    query = """PREFIX dbo: <http://dbpedia.org/ontology/>
            SELECT ?freebaseId
            WHERE
            {
            ?item wdt:P1709 dbo:@dbpedia_class@ ; wdt:P646 ?freebaseId .
            }"""
    query = query.replace("@dbpedia_class@", dbpedia_class)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    try:
        freebase_id = results["results"]["bindings"][0]["freebaseId"]["value"]
    except IndexError:
        print("DBpedia class " + dbpedia_class + " does not exist in Wikidata.")
        return None

    return freebase_id

def get_dbpedia_id_of_freebase_item(freebase_id: str):

    query = """
    PREFIX dbo: <http://dbpedia.org/ontology/>

    SELECT ?article
    WHERE
    {
    ?item wdt:P646 "@freebase_id@" .
    ?article schema:about ?item .
    ?article schema:isPartOf <https://en.wikipedia.org/>.
    }"""

    query = query.replace("@freebase_id@", freebase_id)

    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()

    try:
        wikipedia_id = results["results"]["bindings"][0]["article"]["value"]
        dbpedia_id = wikipedia_id.replace("https://en.wikipedia.org/wiki/","")
    except IndexError:
        print("Freebase ID " + freebase_id + " does not exist in Wikidata.")
        return None

    return dbpedia_id

def is_dbpedia_id_type_of(dbpedia_id: str, dbpedia_class: str):
    query = """
            ASK WHERE {
            <http://dbpedia.org/resource/@dbpedia_id@> rdf:type/rdfs:subClassOf* dbo:@dbpedia_class@ .
            }"""

    query = query.replace("@dbpedia_id@", dbpedia_id)
    query = query.replace("@dbpedia_class@", dbpedia_class)

    sparql_dbpedia.setQuery(query)
    sparql_dbpedia.setReturnFormat(JSON)
    results = sparql_dbpedia.query().convert()

    return results["boolean"]


def retrieve_entities(dbpedia_class:str, geo):
    related_entities = []

    freebase_id = get_freebase_id_of_dbpedia_class(dbpedia_class)
    if not freebase_id:
        return related_entities

    pytrend = TrendReq(hl='en-US', tz=360)

    pytrend.build_payload(kw_list=[freebase_id], geo=geo, timeframe='all')

    res = pytrend.related_topics()[freebase_id]['top']
    if res.empty:
        return related_entities

    # res.to_csv("test.csv")

    res = res.loc[res['topic_type'] != 'Topic']['link']

    for link in res:
        freebase_id = link.replace("/trends/explore?q=","").replace("&date=all&geo="+geo,"")
        print("Check "+freebase_id )
        dbpedia_id = get_dbpedia_id_of_freebase_item(freebase_id)
        if not dbpedia_id:
            continue

        print(" "+dbpedia_id)
        if is_dbpedia_id_type_of(dbpedia_id, dbpedia_class):
            related_entities.append(dbpedia_id)
            print("  -> Yes.")
    return related_entities

results = {}
dbpedia_classes = ["Airport", "Food", "City", "Band", "FilmFestival"]
geos = ["US","RU","DE","IR","FR"]

for dbpedia_class in dbpedia_classes:
    print("\n\n=== "+dbpedia_class+" ===")
    results[dbpedia_class] = {}
    for geo in geos:
        print("\n--- " + geo + " ---")
        results[dbpedia_class][geo] = retrieve_entities(dbpedia_class, geo)

print(results)