from kamidana import as_filter


@as_filter
def surprised(v):
    return "{}!!".format(v)
