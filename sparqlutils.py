from SPARQLWrapper import SPARQLWrapper, JSON
import re

sparql = SPARQLWrapper("http://iccluster052.iccluster.epfl.ch:8899/sparql")
sparql.setReturnFormat(JSON)


def execute_query(query):
    sparql.setQuery(query)
    results = []
    for result in sparql.query().convert()["results"]["bindings"]:
        resultDict = {}
        for key, value in result.items():
            resultDict[key] = value["value"]
        results.append(resultDict)
    return results


def id2url(artComp, solrId):
    journal, day, month, year, page = re.sub(
        r"http://localhost:8080/letemps-data/(...)_(.*?)-(.*?)-(.*?)_Ar0(..).*",
        r'\1;\2;\3;\4;\5', artComp).split(';')
    url = "http://www.letempsarchives.ch/page/%s_%s_%s_%s/%s/article/%s" % (
        journal, year, month, day, page, solrId)
    return url


persons = {}

query = """
SELECT STR(?id) as ?id STR(?issue) AS ?journal STR(?date) AS ?date STR(?name) AS ?personName STR(?firstname) AS ?firstname STR(?lastname) AS ?lastname STR(?function) AS ?function STR(?functionType) AS ?functiontype STR(?nationality) AS ?nationality ?artComp ?solrId
WHERE
{
?pm a lt-owl:PersonMention .
?pm lt-owl:name ?name .
OPTIONAL {?pm lt-owl:firstname ?firstname }
OPTIONAL {?pm lt-owl:lastname ?lastname }
?pm lt-owl:function ?function .
?pm lt-owl:functionType ?functionType .
?pm lt-owl:nationality ?nationality .
?pm lt-owl:mentionedIn ?artComp .
?artComp lt-owl:issueDate ?date .
?artComp lt-owl:publication ?issue .
?artComp lt-owl:articleId ?id.
?artComp dct:title ?title .
?artComp lt-owl:solrId ?solrId
FILTER (!contains(?functionType, "other"))
FILTER (contains(lcase(str(?nationality)), "suisse"))
}
LIMIT 100
"""
query2 = """
SELECT  STR(?issue) AS ?issue STR(?date) AS ?date ?artComp ?solrId ?f ?functionType ?name
WHERE
{
        ?p a lt-owl:PersonMention .
        ?p lt-owl:name ?name  .
        ?p lt-owl:function ?f .
        ?p lt-owl:functionType ?functionType .
        ?p lt-owl:mentionedIn ?artComp .
        ?artComp lt-owl:issueDate ?date .
        ?artComp lt-owl:publication ?issue .
        ?artComp lt-owl:solrId ?solrId .
        BIND (year(?date) AS ?year ).
        FILTER contains(?name, "%s")
        FILTER (!contains(?functionType, "other"))
}
"""
for res in execute_query(query):
    print(query2 % (res['personName']))
    res['articles'] = execute_query(query2 % (res['personName']))
    print(len(res['articles']))
    functions = set()
    for article in res['articles']:
        print(id2url(article['artComp'], article['solrId']))
        functions.add((article['f'].title(), article['functionType']))
    print(functions)
    # print(id2url(res['artComp'],res['solrId']))
