from jinja2 import Template

tmpl = """\
{{word}}|snakecase -> {{word|snakecase}}
"""

t = Template(tmpl, extensions=["kamidana.extensions.NamingHelperExtension"])
print(t.render(word="fooBarBoo"))
