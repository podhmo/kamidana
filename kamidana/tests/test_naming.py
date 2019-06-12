import unittest
from collections import namedtuple


class Tests(unittest.TestCase):
    def test_it(self):
        from kamidana.additionals.naming import camelcase, snakecase, kebabcase

        C = namedtuple("C", "input, fn, output")
        cases = [
            C(input="fooBarBoo", output="fooBarBoo", fn=camelcase),
            C(input="fooBarBoo", output="foo_bar_boo", fn=snakecase),
            C(input="fooBarBoo", output="foo-bar-boo", fn=kebabcase),
        ]
        for c in cases:
            with self.subTest(input=c.input, output=c.output, fn=c.fn):
                got = c.fn(c.input)
                self.assertEqual(got, c.output)
