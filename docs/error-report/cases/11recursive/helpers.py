_RATES = {"USD": 1.0}


def lookup_rate(currency):
    return _RATES[currency]


def format_money(amount, currency):
    rate = lookup_rate(currency)
    return "{} {}".format(round(amount * rate, 2), currency)
