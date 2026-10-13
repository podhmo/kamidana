from kamidana import as_filter
import helpers


@as_filter
def money(amount):
    return helpers.format_money(amount, "JPY")
