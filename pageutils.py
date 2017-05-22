import urllib
import requests
import json
import template
import io
import os


from bs4 import BeautifulSoup

from login import user
from login import passw

summary = 'Wikipastbot update'
baseurl = 'http://wikipast.epfl.ch/wikipast/'

# Login request
payload = {
    'action': 'query',
    'format': 'json',
    'utf8': '',
    'meta': 'tokens',
    'type': 'login'
}
r1 = requests.post(baseurl + 'api.php', data=payload)

# login confirm
login_token = r1.json()['query']['tokens']['logintoken']
payload = {
    'action': 'login',
    'format': 'json',
    'utf8': '',
    'lgname': user,
    'lgpassword': passw,
    'lgtoken': login_token
}
r2 = requests.post(baseurl + 'api.php', data=payload, cookies=r1.cookies)

# get edit token2
params3 = '?format=json&action=query&meta=tokens&continue='
r3 = requests.get(baseurl + 'api.php' + params3, cookies=r2.cookies)
edit_token = r3.json()['query']['tokens']['csrftoken']

edit_cookie = r2.cookies.copy()
edit_cookie.update(r3.cookies)


def commit_changes_to_page(page_name, content, summary):
    # name_ngv = page_name.lower().replace(" ", "%20")
    # content += '[http://dhlabsrv4.epfl.ch/ngviewer.php?mode=1&req_1=' + \
    #    name_ngv + ' ' + page_name + ']\n'
    # content += '=== Archives Le Temps ===\n'
    # save action
    payload = {
        'action': 'edit',
        'assert': 'user',
        'format': 'json',
        'utf8': '',
        'text': content,
        'summary': summary,
        'title': page_name,
        'token': edit_token
    }
    r4 = requests.post(baseurl + 'api.php', data=payload, cookies=edit_cookie)
    print(r4)


def get_page_content(page_name):
    result = requests.post(baseurl + 'api.php?action=query&titles='
                           + page_name +
                           '&export&exportnowrap')
    soup = BeautifulSoup(result.text, "lxml")
    # soup=BeautifulSoup(result.text)
    code = ''
    for primitive in soup.findAll("text"):
        if primitive.string:
            code += primitive.string
    return code


def append_to_page(page_name, content, summary):
    actual_content = get_page_content(page_name)
    commit_changes_to_page(page_name, actual_content+content, summary)

personsAdded = set()
if(os.path.isfile('personsAdded.json')):
    with io.open('personsAdded.json', 'r', encoding='utf-8') as file:
        personsAdded = set(json.load(file))
initLen = len(personsAdded)

def push_pages_from_json(jsonfile, force = False):
    global personsAdded
    with open(jsonfile, 'r') as f:
        peoples = json.load(f)
        print("There is %d"%len(peoples.keys()))
        for pname in sorted(peoples, key=lambda k: len(peoples[k]), reverse=True):
            if(len(personsAdded)-initLen >= 100): break
            mentions = peoples[pname]
            if(not "De" in pname.split(' ')[0] and pname not in personsAdded):
                print("Import %s with %d entries"%(pname, len(mentions)))
                if force or len(get_page_content(pname)) == 0:
                    personsAdded.add(pname)
                    content = template.make_person_page(mentions)
                    commit_changes_to_page(pname, content, "edited by sparql bot")
        print("Imported %d persons in the wiki"%len(list(personsAdded)))
        with io.open('personsAdded.json', 'w', encoding='utf-8') as file:
            json.dump(list(personsAdded), file, ensure_ascii=False)

push_pages_from_json('persons.json')
