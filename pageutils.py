import urllib
import requests
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
        code += primitive.string
    print(code)
    return code


def append_to_page(page_name, content, summary):
    actual_content = get_page_content(page_name)
    commit_changes_to_page(page_name, actual_content+content, summary)
