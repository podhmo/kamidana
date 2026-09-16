from __future__ import annotations

import os.path
import sysconfig
import traceback
from collections import namedtuple
from typing import TYPE_CHECKING

import jinja2

from .._path import is_physical_path

if TYPE_CHECKING:
    import typing as t

# the output shape is a pair of
# - template frames (deduplicated, outermost -> innermost)
# - trailing python frames, dropped when the innermost frame is inside jinja2
Detail = namedtuple("Detail", "jinja2_frames, python_frames")

_JINJA2_DIR = os.path.dirname(jinja2.__file__)
_KAMIDANA_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_STDLIB_DIRS = {
    os.path.realpath(p)
    for p in {sysconfig.get_paths()["stdlib"], sysconfig.get_paths()["platstdlib"]}
}

# names given to the code objects that jinja2 generates for a template
# (see jinja2.debug.rewrite_traceback_stack):
#   "root"          -> "top-level template code"
#   "block_<name>"  -> "block <name>!r" (e.g. "block 'title'")
#   anything else   -> "template"      (macros, loop bodies, ...)
_JINJA2_FRAME_NAMES = frozenset(["template", "top-level template code"])


def _is_jinja2_frame(fs: traceback.FrameSummary) -> bool:
    name = fs.name
    if name in _JINJA2_FRAME_NAMES or name.startswith("block "):
        return True
    return name == "<module>" and fs.filename.endswith((".j2", ".jinja2"))


def _is_jinja2_internal_frame(fs: traceback.FrameSummary) -> bool:
    return os.path.dirname(fs.filename) == _JINJA2_DIR


def _is_internal_python_frame(fs: traceback.FrameSummary) -> bool:
    # frames in stdlib, jinja2, or kamidana itself are not locations the
    # user can act on (e.g. a RecursionError raised inside frozen
    # posixpath during a recursive include)
    if fs.filename.startswith("<frozen"):
        return True
    path = os.path.realpath(fs.filename)
    if any(path.startswith(d + os.sep) for d in _STDLIB_DIRS):
        return True
    return _is_jinja2_internal_frame(fs) or path.startswith(
        _KAMIDANA_DIR + os.sep
    )


def _deduplicate(
    frames: t.List[traceback.FrameSummary],
) -> t.List[traceback.FrameSummary]:
    # collapse render-loop repetition: identical (filename, lineno) frames.
    # same-file frames at different linenos are distinct call sites (e.g. a
    # macro defined and called in one template) and must be kept.
    # physical paths are canonicalized: the entry template may appear as
    # "./x.html" while resolved includes carry absolute paths.
    seen: t.Set[t.Tuple[str, t.Optional[int]]] = set()
    r = []
    for f in reversed(frames):  # innermost -> outermost
        filename = f.filename
        if is_physical_path(filename):
            filename = os.path.realpath(filename)
        k = (filename, f.lineno)
        if k in seen:
            continue
        seen.add(k)
        r.append(f)
    return list(reversed(r))


def extract_detail(exc: Exception) -> Detail:
    frames = traceback.extract_tb(exc.__traceback__)
    jinja2_indices = [i for i, f in enumerate(frames) if _is_jinja2_frame(f)]
    if not jinja2_indices:
        return Detail(jinja2_frames=None, python_frames=None)

    # python frames after the last template frame (e.g. inside a filter
    # function written in python). meaningless when the innermost frame is
    # jinja2's own code.
    python_frames = frames[jinja2_indices[-1] + 1:]
    if python_frames and _is_jinja2_internal_frame(python_frames[-1]):
        python_frames = []

    jinja2_frames = _deduplicate([frames[i] for i in jinja2_indices])
    return Detail(jinja2_frames=jinja2_frames, python_frames=python_frames)
