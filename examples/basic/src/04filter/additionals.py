from kamidana import as_filter


@as_filter
def use(x):
    return oops(x)


def oops(x):
    raise Exception("oops {}".format(x))
