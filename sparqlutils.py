from SPARQLWrapper import SPARQLWrapper, JSON
import os
import io
import json
import re
import urllib
import sys

if(len(sys.argv) < 2):
    print("Need the number of person to look up as argument")
    sys.exit(1)

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

def isValidName(name):
    if len(cleanName(name).split(' ')) < 2:
        return False
    return True

# Cleans a person name
def cleanName(name):
    # We remove every character followed by a '.'
    return re.sub('.\.', '', name.strip()).replace('  ', ' ').title().replace('Mme ', '').replace('Mlle ', '').replace('Dr ', '').strip()


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
        ?pm lt-owl:mentionedIn ?artComp .
        ?artComp lt-owl:issueDate ?date .
        BIND (day(?date) AS ?day ).
        FILTER (!contains(?functionType, "other"))
        FILTER (contains(lcase(str(?nationality)), "suisse"))
        FILTER (?day > 4)
}
LIMIT %s
"""%sys.argv[1]

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
personsAdded = set()
if(os.path.isfile('personsAdded.json')):
    with io.open('personsAdded.json', 'r', encoding='utf-8') as file:
        personsAdded = set(json.load(file))
print("Loaded %d form personsAdded file"%len(personsAdded))
functions = set()
# For each person found
i = 0
for res in execute_query(query):
    i += 1
    # For each article mentioning the person
    if(isValidName(res['personName']) and not res['personName'] in persons and not cleanName(res['personName']) in personsAdded):
        print("Working on %s #%d"%(cleanName(res['personName']),i))
        for article in execute_query(query2 % (res['personName'])):
            functions.add(article['function'])
            article['ref'] = urllib.parse.quote(
            id2url(article['artComp'], article['solrId']) + "/" +
            cleanName(res['personName'])).replace(r'%3A', ':')
            article['journal'] = journals[article['journal']]
            article['nation'] = 'suisse'
            article['date'] = re.sub(r"(....)-(..)-(..).*", r'\1.\2.\3',
                                     article['date'])
            article['name'] = res['personName']
            del article['artComp']
            del article['solrId']
            addMention(article)

# We sort the mention by date
for person, mentions in persons.items():
    print("%s has %d entries"%(person,len(mentions)))
    persons[person] = sorted(mentions, key=lambda k: k['date'])

with io.open('persons.json', 'w', encoding='utf-8') as file:
    json.dump(persons, file, ensure_ascii=False)
