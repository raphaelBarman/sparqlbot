from SPARQLWrapper import SPARQLWrapper, JSON
import io
import json
import re
import urllib

sparql = SPARQLWrapper("http://iccluster052.iccluster.epfl.ch:8899/sparql")
sparql.setReturnFormat(JSON)

journals = {'JDG': "Journal de Genève", "GDL": "Gazette de Lausanne"}


# Executes a query on the sparql endpoint and returns a flattened list of results
def execute_query(query):
    sparql.setQuery(query)
    results = []
    for result in sparql.query().convert()["results"]["bindings"]:
        resultDict = {}
        for key, value in result.items():
            resultDict[key] = value["value"]
        results.append(resultDict)
    return results


# Takes an artComp and sorlId and transforms it into a valid letempsarchives.ch url
def id2url(artComp, solrId):
    journal, day, month, year, page = re.sub(
        r"http://localhost:8080/letemps-data/(...)_(.*?)-(.*?)-(.*?)_Ar0(..).*",
        r'\1;\2;\3;\4;\5', artComp).split(';')
    url = "http://www.letempsarchives.ch/page/%s_%s_%s_%s/%s/article/%s" % (
        journal, year, month, day, page, solrId)
    return url


# Cleans a person name
def cleanName(name):
    # We remove every character followed by a '.'
    return re.sub('.\.', '', name).title().strip()


persons = {}


# Adds a mention for a person
def addMention(mention):
    global persons
    person = cleanName(mention['name'])
    # We do not keep person with only a name/surname
    if len(person.split(' ')) < 2:
        return
    mention['name'] = person
    if person not in persons:
        persons[person] = []
    persons[person].append(mention)


query = """
SELECT STR(?name) AS ?personName STR(?functionType) AS ?functiontype WHERE
{
        ?pm a lt-owl:PersonMention .
        ?pm lt-owl:name ?name .
        ?pm lt-owl:functionType ?functionType .
        ?pm lt-owl:nationality ?nationality .
        FILTER (!contains(?functionType, "other"))
        FILTER (contains(lcase(str(?nationality)), "suisse"))
}
LIMIT 100
"""

query2 = """
SELECT  STR(?issue) AS ?journal STR(?date) AS ?date ?artComp ?solrId ?function ?functionType ?name
WHERE
{
        ?p a lt-owl:PersonMention .
        ?p lt-owl:name ?name  .
        ?p lt-owl:function ?function .
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
# For each person found
for res in execute_query(query):
    # For each article mentioning the person
    for article in execute_query(query2 % (res['personName'])):
        article['ref'] = urllib.parse.quote(
            id2url(article['artComp'], article['solrId']) + "/" +
            cleanName(article['name'])).replace(r'%3A', ':')
        article['journal'] = journals[article['journal']]
        article['nation'] = 'suisse'
        article['date'] = re.sub(r"(....)-(..)-(..).*", r'\1.\2.\3',
                                 article['date'])
        del article['artComp']
        del article['solrId']
        addMention(article)

# We sort the mention by date
for person, mentions in persons.items():
    persons[person] = sorted(mentions, key=lambda k: k['date'])

with io.open('persons.json', 'w', encoding='utf-8') as file:
    json.dump(persons, file, ensure_ascii=False)
