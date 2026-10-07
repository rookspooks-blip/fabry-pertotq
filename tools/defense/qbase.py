SECTIONS = []


def section(key, title, lead):
    SECTIONS.append(dict(key=key, title=title, lead=lead, items=[]))


def Q(question, short, long="", more=""):
    SECTIONS[-1]["items"].append(dict(q=question, short=short, long=long, more=more))
