import os
import sys
import fastentrypoints

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
try:
    with open(os.path.join(here, "README.rst")) as f:
        README = f.read()
    with open(os.path.join(here, "CHANGES.txt")) as f:
        CHANGES = f.read()
except IOError:
    README = CHANGES = ""

install_requires = ["jinja2", "dictknife", "magicalimport", "inflection"]
if sys.version_info[:2] < (3, 7):
    install_requires.append("importlib_resources")

docs_extras = ["sphinx", "recommonmark", "sphinx_rtd_theme"]

tests_require = []

testing_extras = tests_require + []

setup(
    name="kamidana",
    version="0.7.2",
    description="command line jinja2 template (yet another j2cli)",
    long_description=README + "\n\n" + CHANGES,
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: Implementation :: CPython",
    ],
    keywords="jinja2, cli, commandline",
    author="podhmo",
    author_email="ababjam61+github@gmail.com",
    url="https://github.com/podhmo/kamidana",
    packages=find_packages(exclude=["kamidana.tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=install_requires,
    extras_require={"testing": testing_extras, "docs": docs_extras},
    tests_require=tests_require,
    test_suite="kamidana.tests",
    entry_points="""
      [console_scripts]
      kamidana=kamidana.commands.onefile:main
      kamidana-batch=kamidana.commands.manyfiles:main
""",
)
