"""
Reading from other resources (e.g. read_from_file, read_from_command)
"""

import re
import os.path
import subprocess
from kamidana import as_filter
from jinja2 import pass_context
from jinja2.runtime import Context


@as_filter
@pass_context
def read_from_file(ctx: Context, filename: str, *, relative_self: bool = True) -> str:
    if relative_self:
        dirname = os.path.dirname(os.path.abspath(ctx.name or ""))
        filepath = os.path.normpath(os.path.join(dirname, filename))
    else:
        filepath = filename
    with open(filepath) as rf:
        return rf.read()


@as_filter
@pass_context
def read_from_command(
    ctx: Context,
    cmd: str,
    *,
    shell: bool = True,
    check: bool = True,
    encoding: str = "utf-8",
    relative_self: bool = True,
) -> str:
    if relative_self:
        script = "cd {}; {}".format(os.path.dirname(ctx.name or "") or ".", cmd)
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
def strip_ansi_escape_sequence(
    text: str, *, _rx: re.Pattern[str] = re.compile(r"\x1b\[\d+;?\d*m")
) -> str:
    return _rx.sub("", text)
