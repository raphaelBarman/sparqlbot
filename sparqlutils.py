from SPARQLWrapper import SPARQLWrapper, JSON
import re

sparql=SPARQLWrapper("http://iccluster052.iccluster.epfl.ch:8899/sparql")
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
    journal,day,month,year,page = re.sub(r"http://localhost:8080/letemps-data/(...)_(.*?)-(.*?)-(.*?)_Ar0(..).*",r'\1;\2;\3;\4;\5',artComp).split(';')
    url = "http://www.letempsarchives.ch/page/%s_%s_%s_%s/%s/article/%s"%(journal,year,month,day,page,solrId)
    return url


for res in execute_query("""
SELECT STR(?id) as ?ID STR(?issue) AS ?journal STR(?date) AS ?date STR(?name) AS ?personName ?artComp ?solrId
WHERE
{
?pm a lt-owl:PersonMention .
?pm lt-owl:name ?name .
?pm lt-owl:mentionedIn ?artComp .
?artComp lt-owl:issueDate ?date .
?artComp lt-owl:publication ?issue .
?artComp lt-owl:articleId ?id.
?artComp dct:title ?title .
?artComp lt-owl:solrId ?solrId
}
LIMIT 100
"""):
    print(id2url(res['artComp'],res['solrId']))


