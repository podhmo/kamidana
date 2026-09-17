from kamidana import as_filter
from . import helpers


@as_filter
def money(amount):
    return helpers.format_money(amount, "JPY")


@as_filter
def shout(text):
    return helpers.shout(text)
