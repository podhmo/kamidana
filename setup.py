import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.rst")) as f:
    README = f.read()
with open(os.path.join(here, "CHANGES.txt")) as f:
    CHANGES = f.read()

install_requires = [
    "jinja2>=3.1",
    "dictknife[load]>=0.14",
    "inflection>=0.5",
]

docs_extras = ["sphinx", "sphinx_rtd_theme"]

testing_extras = ["pytest"]

setup(
    name="kamidana",
    version=open("VERSION").read().strip(),
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
    long_description_content_type="text/x-rst",
    include_package_data=True,
    zip_safe=False,
    python_requires=">=3.10",
    install_requires=install_requires,
    extras_require={"testing": testing_extras, "docs": docs_extras},
    entry_points="""
      [console_scripts]
      kamidana=kamidana.commands.onefile:main
      kamidana-batch=kamidana.commands.manyfiles:main
""",
)
