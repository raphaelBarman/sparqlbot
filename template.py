
# Templates page generation
mention_entry_template = '[[{date}]]. [[Mention]] de [[{nom}]],[[{fonction}]] [[{nation}]], dans [[{journal}]] [{ref}]'

page_template = """
Page générée automatiquement par le bot sparql

{entries}

"""


def make_content(entries):
    """
    This function create text content from a list of entries dicts each
    containing :
    - date
    - nom
    - fonction
    - nation
    - journal
    - ref (url of the letempsarchives link)
    """
    text = ""
    for entry in entries:
        text += mention_entry_template.format(**entry) + '\n'

    return page_template.format(entries=text)
