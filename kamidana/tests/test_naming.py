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
            C(input="foo_bar_boo", output="fooBarBoo", fn=camelcase),
            C(input="foo_bar_boo", output="foo_bar_boo", fn=snakecase),
            C(input="foo_bar_boo", output="foo-bar-boo", fn=kebabcase),
            C(input="foo-bar-boo", output="fooBarBoo", fn=camelcase),
            C(input="foo-bar-boo", output="foo_bar_boo", fn=snakecase),
            C(input="foo-bar-boo", output="foo-bar-boo", fn=kebabcase),
            C(input="foo-bar_boo", output="fooBarBoo", fn=camelcase),
            C(input="foo-bar_boo", output="foo_bar_boo", fn=snakecase),
            C(input="foo-bar_boo", output="foo-bar-boo", fn=kebabcase),
            C(input="fooBar_boo", output="fooBarBoo", fn=camelcase),
            C(input="fooBar_boo", output="foo_bar_boo", fn=snakecase),
            C(input="fooBar_boo", output="foo-bar-boo", fn=kebabcase),
            C(input="foo_barBoo", output="fooBarBoo", fn=camelcase),
            C(input="foo_barBoo", output="foo_bar_boo", fn=snakecase),
            C(input="foo_barBoo", output="foo-bar-boo", fn=kebabcase),
            C(input="FOObarBoo", output="fOObarBoo", fn=camelcase),
            C(input="FOObarBoo", output="foo_bar_boo", fn=snakecase),
            C(input="FOObarBoo", output="foo-bar-boo", fn=kebabcase),
            C(input="fooBARBoo", output="fooBARBoo", fn=camelcase),
            C(input="fooBARBoo", output="foo_bar_boo", fn=snakecase),
            C(input="fooBARBoo", output="foo-bar-boo", fn=kebabcase),
            C(input="fooBarBOO", output="fooBarBOO", fn=camelcase),
            C(input="fooBarBOO", output="foo_bar_boo", fn=snakecase),
            C(input="fooBarBOO", output="foo-bar-boo", fn=kebabcase),
        ]
        for c in cases:
            with self.subTest(input=c.input, output=c.output, fn=c.fn):
                got = c.fn(c.input)
                self.assertEqual(got, c.output)
