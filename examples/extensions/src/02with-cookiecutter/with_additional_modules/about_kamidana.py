from importlib import resources

from kamidana import as_global


@as_global
def about_kamidana():
    return (
        resources.files("kamidana").joinpath("data.txt").read_text().rstrip()
    )
