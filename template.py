
# Templates page generation
mention_entry_template = '* [[{date}]] / -. [[Mention]] de [[{name}]] en tant que [[{function}]], dans [[{journal}]] [{ref}]'

page_template = """
Page générée automatiquement par le bot sparql

== Mentions ==
{entries}

"""


def make_person_page(entries):
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
