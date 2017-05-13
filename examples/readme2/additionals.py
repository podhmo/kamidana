from kamidana import (
    as_filter,
    as_globals_generator,
    as_test,
)


@as_filter
def surprised(v):
    return "{}!!".format(v)


@as_globals_generator
def generate_globals():
    return {"daytime": "hello", "night": "bye"}


@as_test
def night(hour):
    return 19 <= hour or hour < 3
