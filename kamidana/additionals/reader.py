"""
Reading from other resources (e.g. read_from_file, read_from_command)
"""
import re
import os.path
import subprocess
from kamidana import as_filter
from jinja2.filters import contextfilter


@as_filter
@contextfilter
def read_from_file(ctx, filename, *, relative_self=True):
    if relative_self:
        dirname = os.path.dirname(os.path.abspath(ctx.name))
        filepath = os.path.normpath(os.path.join(dirname, filename))
    else:
        filepath = filename
    with open(filepath) as rf:
        return rf.read()


@as_filter
@contextfilter
def read_from_command(
    ctx, cmd, *, shell=True, check=True, encoding="utf-8", relative_self=True
):
    if relative_self:
        script = "cd {}; {}".format(os.path.dirname(ctx.name) or ".", cmd)
    else:
        script = cmd
    p = subprocess.run(
        script,
        shell=shell,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    return p.stdout


@as_filter
def strip_ansi_escape_sequence(text, *, _rx=re.compile(r"\x1b\[\d+;?\d*m")):
    return _rx.sub("", text)
