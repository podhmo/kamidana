"""domain logic living outside the template layer."""

_RATES = {"USD": 1.0, "EUR": 1.1}


def lookup_rate(currency):
    return _RATES[currency]


def format_money(amount, currency):
    rate = lookup_rate(currency)
    return "{} {}".format(round(amount * rate, 2), currency)
