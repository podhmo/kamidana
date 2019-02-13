from kamidana import as_filter


@as_filter
def scream(s):
    return s.upper()
