import subprocess
from kamidana import as_filter


@as_filter
def read(filename):
    with open(filename) as rf:
        return rf.read()


@as_filter
def spawn(cmd, encoding="utf-8"):
    p = subprocess.run(
        cmd,
        shell=True,
        check=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return p.stdout.decode(encoding)
