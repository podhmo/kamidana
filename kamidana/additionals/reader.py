import subprocess
from kamidana import as_filter


@as_filter
def read_from_file(filename):
    with open(filename) as rf:
        return rf.read()


@as_filter
def read_from_command(cmd, *, shell=True, check=True, encoding="utf-8"):
    p = subprocess.run(
        cmd,
        shell=shell,
        check=check,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    return p.stdout.decode(encoding)
